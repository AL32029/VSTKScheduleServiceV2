CREATE OR REPLACE FUNCTION check_lesson_updates(
    p_from    date,
    p_to      date,
    p_lessons jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
AS
$$
DECLARE
    v_g_published jsonb;
    v_g_modified  jsonb;
    v_g_deleted   jsonb;
    v_c_published jsonb;
    v_c_modified  jsonb;
    v_c_deleted   jsonb;
BEGIN
    IF jsonb_typeof(p_lessons) <> 'array' THEN
        RAISE EXCEPTION 'lessons must be a JSON array, got %', jsonb_typeof(p_lessons);
    END IF;

    IF jsonb_array_length(p_lessons) = 0 THEN
        RAISE EXCEPTION 'lessons array is empty';
    END IF;

    IF p_from > p_to THEN
        RAISE EXCEPTION 'period start must be <= period end';
    END IF;

    DROP TABLE IF EXISTS _l_input      CASCADE;
    DROP TABLE IF EXISTS _l_existing   CASCADE;
    DROP TABLE IF EXISTS _l_to_delete  CASCADE;
    DROP TABLE IF EXISTS _l_to_update  CASCADE;
    DROP TABLE IF EXISTS _l_to_insert  CASCADE;
    DROP TABLE IF EXISTS _l_insert_map CASCADE;
    DROP TABLE IF EXISTS _c_existing   CASCADE;
    DROP TABLE IF EXISTS _c_input      CASCADE;

    CREATE TEMP TABLE _l_input (
        input_id        serial PRIMARY KEY,
        group_index     text,
        lesson_at       date,
        lesson_start    time,
        lesson_end      time,
        time_range_id   int,
        title_indexes   text[],
        cabinet_indexes text[]
    ) ON COMMIT DROP;

    INSERT INTO _l_input (
        group_index, lesson_at, lesson_start, lesson_end,
        time_range_id, title_indexes, cabinet_indexes
    )
    SELECT
        elem->>'group_index',
        p_from + d.day_offset,
        (elem->'time_range'->>'start')::time,
        (elem->'time_range'->>'end')::time,
        lt.id,
        ARRAY(SELECT jsonb_array_elements_text(COALESCE(elem->'titles',   '[]'::jsonb))),
        ARRAY(SELECT jsonb_array_elements_text(COALESCE(elem->'cabinets', '[]'::jsonb)))
      FROM jsonb_array_elements(p_lessons) AS elem
      CROSS JOIN generate_series(0, (p_to - p_from)) AS d(day_offset)
      LEFT JOIN lesson_times lt
             ON lt.active_until IS NULL
            AND lt.lesson_start = (elem->'time_range'->>'start')::time
            AND lt.lesson_end   = (elem->'time_range'->>'end')::time;

    IF EXISTS (SELECT 1 FROM _l_input WHERE time_range_id IS NULL) THEN
        RAISE EXCEPTION 'some lessons reference time ranges that are not active';
    END IF;

    IF EXISTS (
        SELECT 1 FROM _l_input
        GROUP BY group_index, lesson_start, lesson_end
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'duplicate (group_index, lesson_start, lesson_end) in input';
    END IF;

    IF EXISTS (
        SELECT 1 FROM _l_input i
         WHERE NOT EXISTS (SELECT 1 FROM groups g WHERE g.index = i.group_index)
    ) THEN
        RAISE EXCEPTION 'some groups are not present in the groups table';
    END IF;

    IF EXISTS (
        SELECT 1 FROM _l_input i
        CROSS JOIN LATERAL unnest(i.title_indexes) AS t(title_index)
         WHERE NOT EXISTS (SELECT 1 FROM lesson_titles lt WHERE lt.index = t.title_index)
    ) THEN
        RAISE EXCEPTION 'some lesson titles are not present in the lesson_titles table';
    END IF;

    IF EXISTS (
        SELECT 1 FROM _l_input i
        CROSS JOIN LATERAL unnest(i.cabinet_indexes) AS c(cabinet_index)
         WHERE NOT EXISTS (SELECT 1 FROM cabinets c2 WHERE c2.index = c.cabinet_index)
    ) THEN
        RAISE EXCEPTION 'some cabinets are not present in the cabinets table';
    END IF;

    CREATE TEMP TABLE _l_existing (
        lesson_id       int PRIMARY KEY,
        group_index     text,
        lesson_at       date,
        lesson_start    time,
        time_range_id   int,
        title_indexes   text[],
        cabinet_indexes text[]
    ) ON COMMIT DROP;

    INSERT INTO _l_existing
    SELECT
        l.id,
        l.group_index,
        l.lesson_at,
        lt.lesson_start,
        l.time_range_id,
        COALESCE(
            (SELECT array_agg(x.lesson_title_id ORDER BY x.lesson_title_index)
               FROM lesson_lesson_titles x
              WHERE x.lesson_id = l.id),
            ARRAY[]::text[]),
        COALESCE(
            (SELECT array_agg(x.cabinet_id ORDER BY x.cabinet_index)
               FROM lesson_cabinets x
              WHERE x.lesson_id = l.id),
            ARRAY[]::text[])
      FROM lessons l
      JOIN lesson_times lt ON lt.id = l.time_range_id
     WHERE l.lesson_at BETWEEN p_from AND p_to;

    CREATE TEMP TABLE _l_to_delete ON COMMIT DROP AS
    SELECT e.lesson_id, e.group_index, e.lesson_start
      FROM _l_existing e
     WHERE NOT EXISTS (
         SELECT 1 FROM _l_input i
          WHERE i.group_index  = e.group_index
            AND i.lesson_at    = e.lesson_at
            AND i.lesson_start = e.lesson_start
     );

    CREATE TEMP TABLE _l_to_update ON COMMIT DROP AS
    SELECT e.lesson_id,
           e.group_index,
           e.lesson_start,
           i.input_id,
           i.time_range_id   AS new_time_range_id,
           i.title_indexes   AS new_title_indexes,
           i.cabinet_indexes AS new_cabinet_indexes
      FROM _l_existing e
      JOIN _l_input    i
        ON i.group_index  = e.group_index
       AND i.lesson_at    = e.lesson_at
       AND i.lesson_start = e.lesson_start
     WHERE e.time_range_id   <> i.time_range_id
        OR e.title_indexes   IS DISTINCT FROM i.title_indexes
        OR e.cabinet_indexes IS DISTINCT FROM i.cabinet_indexes;

    CREATE TEMP TABLE _l_to_insert ON COMMIT DROP AS
    SELECT i.*
      FROM _l_input i
     WHERE NOT EXISTS (
         SELECT 1 FROM _l_existing e
          WHERE e.group_index  = i.group_index
            AND e.lesson_at    = i.lesson_at
            AND e.lesson_start = i.lesson_start
     );

    CREATE TEMP TABLE _c_existing ON COMMIT DROP AS
    SELECT DISTINCT
           c.cabinet_id AS cabinet_index,
           e.group_index,
           e.lesson_at,
           e.lesson_start
      FROM _l_existing e
      CROSS JOIN LATERAL unnest(e.cabinet_indexes) AS c(cabinet_id);

    CREATE TEMP TABLE _c_input ON COMMIT DROP AS
    SELECT DISTINCT
           c.cabinet_id AS cabinet_index,
           i.group_index,
           i.lesson_at,
           i.lesson_start
      FROM _l_input i
      CROSS JOIN LATERAL unnest(i.cabinet_indexes) AS c(cabinet_id);

    DELETE FROM lessons WHERE id IN (SELECT lesson_id FROM _l_to_delete);

    UPDATE lessons
       SET time_range_id = u.new_time_range_id
      FROM _l_to_update u
     WHERE lessons.id = u.lesson_id;

    DELETE FROM lesson_cabinets
     WHERE lesson_id IN (SELECT lesson_id FROM _l_to_update);

    DELETE FROM lesson_lesson_titles
     WHERE lesson_id IN (SELECT lesson_id FROM _l_to_update);

    INSERT INTO lesson_cabinets (lesson_id, cabinet_id, cabinet_index)
    SELECT u.lesson_id,
           c.cabinet_id,
           (c.ord - 1)::smallint
      FROM _l_to_update u
      CROSS JOIN LATERAL unnest(u.new_cabinet_indexes) WITH ORDINALITY AS c(cabinet_id, ord);

    INSERT INTO lesson_lesson_titles (lesson_id, lesson_title_id, lesson_title_index)
    SELECT u.lesson_id,
           t.title_id,
           (t.ord - 1)::smallint
      FROM _l_to_update u
      CROSS JOIN LATERAL unnest(u.new_title_indexes) WITH ORDINALITY AS t(title_id, ord);

    CREATE TEMP TABLE _l_insert_map (
        input_id  int PRIMARY KEY,
        lesson_id int
    ) ON COMMIT DROP;

    WITH ins AS (
        INSERT INTO lessons (lesson_at, group_index, time_range_id)
        SELECT lesson_at, group_index, time_range_id FROM _l_to_insert
        RETURNING id, group_index, lesson_at, time_range_id
    )
    INSERT INTO _l_insert_map (input_id, lesson_id)
    SELECT ti.input_id, ins.id
      FROM ins
      JOIN _l_to_insert ti
        ON ti.group_index   = ins.group_index
       AND ti.lesson_at     = ins.lesson_at
       AND ti.time_range_id = ins.time_range_id;

    INSERT INTO lesson_cabinets (lesson_id, cabinet_id, cabinet_index)
    SELECT m.lesson_id,
           c.cabinet_id,
           (c.ord - 1)::smallint
      FROM _l_insert_map m
      JOIN _l_input      i ON i.input_id = m.input_id
      CROSS JOIN LATERAL unnest(i.cabinet_indexes) WITH ORDINALITY AS c(cabinet_id, ord);

    INSERT INTO lesson_lesson_titles (lesson_id, lesson_title_id, lesson_title_index)
    SELECT m.lesson_id,
           t.title_id,
           (t.ord - 1)::smallint
      FROM _l_insert_map m
      JOIN _l_input      i ON i.input_id = m.input_id
      CROSS JOIN LATERAL unnest(i.title_indexes) WITH ORDINALITY AS t(title_id, ord);

    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object('index', g.index, 'number', g.number)
                   ORDER BY g.index
               ),
               '[]'::jsonb)
      INTO v_g_published
      FROM groups g
     WHERE g.index IN (
         SELECT DISTINCT group_index FROM _l_input
         EXCEPT
         SELECT DISTINCT group_index FROM _l_existing
     );

    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object('index', g.index, 'number', g.number)
                   ORDER BY g.index
               ),
               '[]'::jsonb)
      INTO v_g_deleted
      FROM groups g
     WHERE g.index IN (
         SELECT DISTINCT group_index FROM _l_existing
         EXCEPT
         SELECT DISTINCT group_index FROM _l_input
     );

    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object('index', g.index, 'number', g.number)
                   ORDER BY g.index
               ),
               '[]'::jsonb)
      INTO v_g_modified
      FROM groups g
     WHERE g.index IN (
         SELECT DISTINCT x.group_index
           FROM (
               SELECT group_index FROM _l_to_delete
               UNION
               SELECT group_index FROM _l_to_update
               UNION
               SELECT group_index FROM _l_to_insert
           ) x
          WHERE x.group_index IN (SELECT group_index FROM _l_input)
            AND x.group_index IN (SELECT group_index FROM _l_existing)
     );

    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object('index', c.index, 'number', c.number)
                   ORDER BY c.index
               ),
               '[]'::jsonb)
      INTO v_c_published
      FROM cabinets c
     WHERE c.index IN (
         SELECT DISTINCT cabinet_index FROM _c_input
         EXCEPT
         SELECT DISTINCT cabinet_index FROM _c_existing
     );

    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object('index', c.index, 'number', c.number)
                   ORDER BY c.index
               ),
               '[]'::jsonb)
      INTO v_c_deleted
      FROM cabinets c
     WHERE c.index IN (
         SELECT DISTINCT cabinet_index FROM _c_existing
         EXCEPT
         SELECT DISTINCT cabinet_index FROM _c_input
     );

    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object('index', c.index, 'number', c.number)
                   ORDER BY c.index
               ),
               '[]'::jsonb)
      INTO v_c_modified
      FROM cabinets c
     WHERE c.index IN (
         SELECT DISTINCT d.cabinet_index
           FROM (
               (SELECT cabinet_index, group_index, lesson_at, lesson_start FROM _c_existing
                EXCEPT
                SELECT cabinet_index, group_index, lesson_at, lesson_start FROM _c_input)
               UNION
               (SELECT cabinet_index, group_index, lesson_at, lesson_start FROM _c_input
                EXCEPT
                SELECT cabinet_index, group_index, lesson_at, lesson_start FROM _c_existing)
           ) d
          WHERE d.cabinet_index IN (SELECT cabinet_index FROM _c_input)
            AND d.cabinet_index IN (SELECT cabinet_index FROM _c_existing)
     );

    RETURN jsonb_build_object(
        'groups', jsonb_build_object(
            'published', v_g_published,
            'modified',  v_g_modified,
            'deleted',   v_g_deleted
        ),
        'cabinets', jsonb_build_object(
            'published', v_c_published,
            'modified',  v_c_modified,
            'deleted',   v_c_deleted
        )
    );
END;
$$;