CREATE OR REPLACE FUNCTION check_group_updates(groups jsonb)
RETURNS jsonb
LANGUAGE plpgsql
AS
$$
DECLARE
    indexes       text[];
    v_deactivated jsonb;
    v_activated   jsonb;
    v_inserted    jsonb;
BEGIN
    IF jsonb_typeof(groups) <> 'array' THEN
        RAISE EXCEPTION 'groups must be a JSON array, got %', jsonb_typeof(groups);
    END IF;

    SELECT COALESCE(array_agg(elem->>'index'), '{}')
      INTO indexes
      FROM jsonb_array_elements(groups) AS elem;

    WITH upd AS (
        UPDATE groups
           SET is_active = false
         WHERE is_active = true
           AND index <> ALL (indexes)
        RETURNING index, number
    )
    SELECT COALESCE(
             jsonb_agg(jsonb_build_object('index', index, 'number', number)
                       ORDER BY index),
             '[]'::jsonb)
      INTO v_deactivated
      FROM upd;

    WITH upd AS (
        UPDATE groups
           SET is_active = true
         WHERE is_active = false
           AND index = ANY (indexes)
        RETURNING index, number
    )
    SELECT COALESCE(
             jsonb_agg(jsonb_build_object('index', index, 'number', number)
                       ORDER BY index),
             '[]'::jsonb)
      INTO v_activated
      FROM upd;

    WITH ins AS (
        INSERT INTO groups (index, number, is_active)
        SELECT elem->>'index', elem->>'number', true
          FROM jsonb_array_elements(groups) AS elem
         WHERE NOT EXISTS (
             SELECT 1 FROM groups g WHERE g.index = elem->>'index'
         )
        RETURNING index, number
    )
    SELECT COALESCE(
             jsonb_agg(jsonb_build_object('index', index, 'number', number)
                       ORDER BY index),
             '[]'::jsonb)
      INTO v_inserted
      FROM ins;

    RETURN jsonb_build_object(
        'deactivated', v_deactivated,
        'activated',   v_activated,
        'inserted',    v_inserted
    );
END;
$$;