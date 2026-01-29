-- This program checks all schemas for timescaledb hypertables called
-- `observation`, renames these tables to `observation_old` and copies
-- all data to a structurally identical postgres table.
-- NOTE: To finisch the migration the hypertables called `observation_old`
--       need to be removed manually.
DO $$
DECLARE
    schema_name text;
    table_exists boolean;
    is_hypertable boolean;
BEGIN
    FOR schema_name IN
        SELECT nspname
        FROM pg_namespace
        WHERE nspname NOT IN ('pg_catalog', 'information_schema')
          AND has_schema_privilege(nspname, 'USAGE')
    LOOP
        -- Step 1: Check if observation table exists
        SELECT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = schema_name AND tablename = 'observation'
        ) INTO table_exists;

        IF table_exists THEN
            -- Step 2: Check if it's a hypertable
            SELECT EXISTS (
                SELECT 1 FROM timescaledb_information.hypertables
                WHERE hypertable_schema = schema_name AND hypertable_name = 'observation'
            ) INTO is_hypertable;

            IF is_hypertable THEN
                RAISE NOTICE 'Migrating schema: %', schema_name;

                -- Step 3: If already renamed, skip
                IF EXISTS (
                    SELECT 1 FROM pg_tables
                    WHERE schemaname = schema_name AND tablename = 'observation_old'
                ) THEN
                    RAISE NOTICE 'Schema % seems to be partially migrated, as there are two hypertables called observation and observation_old. Skipping, but please check!', schema_name;
                    CONTINUE;
                END IF;

                -- Step 4: Rename the hypertable to observation_old
                EXECUTE format('ALTER TABLE %I.observation RENAME TO observation_old', schema_name);

                -- Step 5: Create regular table with same structure
                EXECUTE format('CREATE TABLE %I.observation (LIKE %I.observation_old INCLUDING ALL)', schema_name, schema_name);

                -- Step 6: Copy all data
                EXECUTE format('INSERT INTO %I.observation SELECT * FROM %I.observation_old', schema_name, schema_name);

                RAISE NOTICE 'Successfully migrated observation table in schema %.', schema_name;
            ELSE
                RAISE NOTICE 'Table observation in schema % is not a hypertable, skipping.', schema_name;
            END IF;
        END IF;
    END LOOP;
END $$;
