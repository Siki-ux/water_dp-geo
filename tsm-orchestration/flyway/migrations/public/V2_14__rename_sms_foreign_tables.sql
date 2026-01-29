DO
$$
    DECLARE
        table_names text[] := ARRAY [
            'sms_contact',
            'sms_configuration',
            'sms_configuration_contact_role',
            'sms_configuration_dynamic_location_begin_action',
            'sms_configuration_static_location_begin_action',
            'sms_device',
            'sms_device_mount_action',
            'sms_device_property',
            'sms_device_contact_role',
            'sms_datastream_link'
            ];
        table_name  text;
    BEGIN
        IF '${sms_access_type}' = 'db' THEN
            RAISE NOTICE 'Renaming foreign tables of sms in order to use materialized views instead';
            FOREACH table_name IN ARRAY table_names
                LOOP
                    IF EXISTS (SELECT 1
                               FROM information_schema.foreign_tables
                               WHERE foreign_table_name = table_name
                                 AND foreign_table_schema = 'public') THEN
                        EXECUTE format('ALTER FOREIGN TABLE public.%s RENAME TO foreign_table_%s;', table_name,
                                       table_name);
                        RAISE NOTICE 'Renamed foreign table % ', table_name;
                    ELSE
                        RAISE NOTICE 'Foreign table % does not exist, skipping rename', table_name;
                    END IF;
                END LOOP;
        ELSE
            RAISE NOTICE 'Skipping renaming of foreign tables for sms because sms_access_type is not db';
        END IF;
    END
$$;