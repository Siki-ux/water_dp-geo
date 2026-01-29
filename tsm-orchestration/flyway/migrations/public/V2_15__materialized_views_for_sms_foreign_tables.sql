DO
$$
    DECLARE
        table_names            text[] := ARRAY [
            'contact',
            'configuration',
            'configuration_contact_role',
            'configuration_dynamic_location_begin_action',
            'configuration_static_location_begin_action',
            'device',
            'device_contact_role',
            'device_mount_action',
            'device_property',
            'datastream_link'
            ];
        table_name             text;
        ft_name                text;
        materialized_view_name text;
    BEGIN
        IF '${sms_access_type}' = 'db' THEN
            RAISE NOTICE 'Creating materialized views for foreign tables of sms';
            FOREACH table_name IN ARRAY table_names
                LOOP
                    ft_name := 'foreign_table_sms_' || table_name;
                    materialized_view_name := 'sms_' || table_name;

                    IF EXISTS (SELECT 1
                               FROM information_schema.foreign_tables
                               WHERE foreign_table_name = ft_name
                                 AND foreign_table_schema = 'public') THEN
                        EXECUTE format('CREATE MATERIALIZED VIEW public.%s AS SELECT * FROM public.%s;',
                                       materialized_view_name, ft_name);
                        EXECUTE format('CREATE UNIQUE INDEX %s_pkey ON public.%s (id);', materialized_view_name,
                                       materialized_view_name);
                        RAISE NOTICE 'Created materialized view %s and index on primary key', materialized_view_name;
                    ELSE
                        RAISE NOTICE 'Foreign table %s does not exist, skipping materialized view creation', ft_name;
                    END IF;
                END LOOP;
        ELSE
            RAISE NOTICE 'Skipping creating materialized views for sms because sms_access_type is not db';
        END IF;
    END
$$;