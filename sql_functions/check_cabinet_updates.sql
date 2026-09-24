CREATE OR REPLACE FUNCTION check_cabinet_updates(cabinets jsonb)
RETURNS jsonb
LANGUAGE plpgsql
AS
$$
DECLARE
    v_inserted jsonb;
BEGIN
    IF jsonb_typeof(cabinets) <> 'array' THEN
        RAISE EXCEPTION 'cabinets must be a JSON array, got %', jsonb_typeof(cabinets);
    END IF;

    WITH ins AS (
        INSERT INTO cabinets (index, number)
        SELECT elem->>'index', elem->>'number'
          FROM jsonb_array_elements(cabinets) AS elem
         WHERE NOT EXISTS (
             SELECT 1 FROM cabinets c WHERE c.index = elem->>'index'
         )
        RETURNING index, number
    )
    SELECT COALESCE(
             jsonb_agg(jsonb_build_object('index', index, 'number', number)
                       ORDER BY index),
             '[]'::jsonb)
      INTO v_inserted
      FROM ins;

    RETURN jsonb_build_object('inserted', v_inserted);
END;
$$;