CREATE OR REPLACE FUNCTION check_lesson_time_updates(times jsonb)
RETURNS jsonb
LANGUAGE plpgsql
AS
$$
DECLARE
    v_inserted  jsonb;
    v_closed    jsonb;
    v_unchanged jsonb;
BEGIN
    IF jsonb_typeof(times) <> 'array' THEN
        RAISE EXCEPTION 'times must be a JSON array, got %', jsonb_typeof(times);
    END IF;

    IF jsonb_array_length(times) = 0 THEN
        RAISE EXCEPTION 'times array is empty; refusing to close all active rows';
    END IF;

    WITH input AS (
        SELECT elem->>'time_type'            AS time_type,
               (elem->>'lesson_start')::time AS lesson_start,
               (elem->>'lesson_end')::time   AS lesson_end
          FROM jsonb_array_elements(times) AS elem
    )
    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object(
                       'id',           lt.id,
                       'time_type',    lt.time_type,
                       'lesson_start', to_char(lt.lesson_start, 'HH24:MI'),
                       'lesson_end',   to_char(lt.lesson_end,   'HH24:MI')
                   )
                   ORDER BY lt.time_type, lt.lesson_start
               ),
               '[]'::jsonb)
      INTO v_unchanged
      FROM lesson_times lt
      JOIN input i
        ON i.time_type    = lt.time_type
       AND i.lesson_start = lt.lesson_start
       AND i.lesson_end   = lt.lesson_end
     WHERE lt.active_until IS NULL;

    WITH closed AS (
        UPDATE lesson_times lt
           SET active_until = now()
         WHERE lt.active_until IS NULL
           AND NOT EXISTS (
               SELECT 1
                 FROM jsonb_array_elements(times) AS elem
                WHERE elem->>'time_type'            = lt.time_type
                  AND (elem->>'lesson_start')::time = lt.lesson_start
                  AND (elem->>'lesson_end')::time   = lt.lesson_end
           )
        RETURNING lt.id, lt.time_type, lt.lesson_start, lt.lesson_end
    )
    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object(
                       'id',           id,
                       'time_type',    time_type,
                       'lesson_start', to_char(lesson_start, 'HH24:MI'),
                       'lesson_end',   to_char(lesson_end,   'HH24:MI')
                   )
                   ORDER BY time_type, lesson_start
               ),
               '[]'::jsonb)
      INTO v_closed
      FROM closed;

    WITH input AS (
        SELECT elem->>'time_type'            AS time_type,
               (elem->>'lesson_start')::time AS lesson_start,
               (elem->>'lesson_end')::time   AS lesson_end
          FROM jsonb_array_elements(times) AS elem
    ),
    ins AS (
        INSERT INTO lesson_times (time_type, lesson_start, lesson_end, active_from)
        SELECT i.time_type, i.lesson_start, i.lesson_end, now()
          FROM input i
         WHERE NOT EXISTS (
             SELECT 1
               FROM lesson_times lt
              WHERE lt.active_until IS NULL
                AND lt.time_type    = i.time_type
                AND lt.lesson_start = i.lesson_start
                AND lt.lesson_end   = i.lesson_end
         )
        ON CONFLICT (time_type, lesson_start) WHERE active_until IS NULL DO NOTHING
        RETURNING id, time_type, lesson_start, lesson_end
    )
    SELECT COALESCE(
               jsonb_agg(
                   jsonb_build_object(
                       'id',           id,
                       'time_type',    time_type,
                       'lesson_start', to_char(lesson_start, 'HH24:MI'),
                       'lesson_end',   to_char(lesson_end,   'HH24:MI')
                   )
                   ORDER BY time_type, lesson_start
               ),
               '[]'::jsonb)
      INTO v_inserted
      FROM ins;

    RETURN jsonb_build_object(
        'inserted',  v_inserted,
        'closed',    v_closed,
        'unchanged', v_unchanged
    );
END;
$$;