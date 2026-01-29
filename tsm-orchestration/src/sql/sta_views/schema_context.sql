CREATE OR REPLACE function public.get_schema_org_context() RETURNS jsonb AS
$$
BEGIN
    RETURN
        '{
          "@version": "1.1",
          "@import": "stamplate.jsonld",
          "@vocab": "http://schema.org/"
        }'::jsonb;
END;
$$ language plpgsql;
