-- This program adds a primary key column called `id` to the `observation` tables in all schemas.
-- NOTE: For large tables this might take up to a few hours.
DO $$
DECLARE
    r RECORD;
    full_table TEXT;
    tbl_name TEXT := 'observation';
    seq_name TEXT;
    constraint_name TEXT;
    max_id BIGINT;
BEGIN
    FOR r IN
        SELECT table_schema
        FROM information_schema.tables
        WHERE table_name = tbl_name
          AND table_type = 'BASE TABLE'
    LOOP
        full_table := quote_ident(r.table_schema) || '.' || quote_ident(tbl_name);
        seq_name := quote_ident(r.table_schema) || '.' || quote_ident('observation_id_seq');
        constraint_name := quote_ident('pk_observation');

        RAISE NOTICE 'Processing schema: %', r.table_schema;

        -- Check if 'id' column exists
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = r.table_schema
              AND table_name = tbl_name
              AND column_name = 'id'
        ) THEN
            RAISE NOTICE 'Adding id column to table %', full_table;
            EXECUTE format('ALTER TABLE %s ADD COLUMN id BIGINT;', full_table);

            RAISE NOTICE 'Creating sequence %', seq_name;
            EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %s;', seq_name);

            RAISE NOTICE 'Resetting sequence to start from 1...';
            EXECUTE format('SELECT setval(''%s'', 1, false);', r.table_schema || '.observation_id_seq');

            RAISE NOTICE 'Populating id values...';
            EXECUTE format(
                'UPDATE %s SET id = nextval(''%s'') WHERE id IS NULL;',
                full_table, r.table_schema || '.observation_id_seq'
            );

            RAISE NOTICE 'Fetching max id for %', full_table;
            EXECUTE format('SELECT MAX(id) FROM %s;', full_table) INTO max_id;
            IF max_id IS NULL THEN
                max_id := 1;
            END IF;

            RAISE NOTICE 'Setting sequence to current max id: %', max_id;
            EXECUTE format('SELECT setval(''%s'', %s, true);', r.table_schema || '.observation_id_seq', max_id);

            RAISE NOTICE 'Setting default for id column...';
            EXECUTE format(
                'ALTER TABLE %s ALTER COLUMN id SET DEFAULT nextval(''%s'');',
                full_table, r.table_schema || '.observation_id_seq'
            );

            RAISE NOTICE 'Setting sequence ownership...';
            EXECUTE format(
                'ALTER SEQUENCE %s OWNED BY %s.id;',
                seq_name, full_table
            );

            RAISE NOTICE 'Adding primary key constraint...';
            EXECUTE format(
                'ALTER TABLE %s ADD CONSTRAINT %s PRIMARY KEY (id);',
                full_table, constraint_name
            );
        ELSE
            RAISE NOTICE 'Table % already has an id column. Skipping.', full_table;
        END IF;
    END LOOP;
END
$$;
