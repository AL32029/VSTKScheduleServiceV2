CREATE OR REPLACE FUNCTION get_all_groups()
	RETURNS jsonb
	LANGUAGE sql
	STABLE
AS
$$
SELECT jsonb_agg(
		       jsonb_build_object(
				       'index', g.index,
				       'number', g.number,
				       'is_active', g.is_active
		       )
		       ORDER BY g.index
       )
FROM groups g;
$$;