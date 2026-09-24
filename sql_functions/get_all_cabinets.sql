CREATE OR REPLACE FUNCTION get_all_cabinets()
	RETURNS jsonb
	LANGUAGE sql
	STABLE
AS
$$
SELECT jsonb_agg(
		       jsonb_build_object(
				       'index', c.index,
				       'number', c.number
		       )
		       ORDER BY c.index
       )
FROM cabinets c;
$$;