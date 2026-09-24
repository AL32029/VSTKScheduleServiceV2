CREATE OR REPLACE FUNCTION check_lesson_title_updates(titles jsonb)
RETURNS jsonb
LANGUAGE plpgsql
AS
$$
DECLARE
    v_inserted jsonb;
    v_updated  jsonb;
BEGIN
    IF jsonb_typeof(titles) <> 'array' THEN
        RAISE EXCEPTION 'titles must be a JSON array, got %', jsonb_typeof(titles);
    END IF;

    WITH upd AS (
        UPDATE lesson_titles t
           SET custom_title = elem->>'custom_title'
          FROM jsonb_array_elements(titles) AS elem
         WHERE t.index = elem->>'index'
           AND COALESCE(t.custom_title, '') IS DISTINCT FROM COALESCE(elem->>'custom_title', '')
        RETURNING t.index, t.original_title, t.custom_title
    )
    SELECT COALESCE(
             jsonb_agg(
                 jsonb_build_object(
                     'index',          index,
                     'original_title', original_title,
                     'custom_title',   custom_title
                 )
                 ORDER BY index
             ),
             '[]'::jsonb)
      INTO v_updated
      FROM upd;

    WITH ins AS (
        INSERT INTO lesson_titles (index, original_title, custom_title, is_countable)
        SELECT elem->>'index',
               elem->>'original_title',
               elem->>'custom_title',
               COALESCE((elem->>'is_countable')::boolean, true)
          FROM jsonb_array_elements(titles) AS elem
        ON CONFLICT (index) DO NOTHING
        RETURNING index, original_title, custom_title
    )
    SELECT COALESCE(
             jsonb_agg(
                 jsonb_build_object(
                     'index',          index,
                     'original_title', original_title,
                     'custom_title',   custom_title
                 )
                 ORDER BY index
             ),
             '[]'::jsonb)
      INTO v_inserted
      FROM ins;

    RETURN jsonb_build_object(
        'inserted', v_inserted,
        'updated',  v_updated
    );
END;
$$;