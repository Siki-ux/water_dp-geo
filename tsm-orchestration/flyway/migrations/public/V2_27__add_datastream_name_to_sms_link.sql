-- Purpose: Repair V2_26 collision with legacy Materialized Views and add new column.
-- We must convert sms_ stubs from Materialized Views to real Tables.

DO $$
BEGIN
    -- 1. Handle sms_datastream_link
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'sms_datastream_link') THEN
        DROP MATERIALIZED VIEW public.sms_datastream_link;
    END IF;
    
    CREATE TABLE IF NOT EXISTS public.sms_datastream_link (
        id SERIAL PRIMARY KEY,
        thing_id UUID,
        device_property_id INTEGER,
        device_mount_action_id INTEGER,
        datasource_id VARCHAR(256),
        datastream_id INTEGER,
        datastream_name VARCHAR(256),
        begin_date TIMESTAMP WITH TIME ZONE,
        end_date TIMESTAMP WITH TIME ZONE,
        aggregation_period DOUBLE PRECISION,
        license_uri VARCHAR(256),
        license_name VARCHAR(256),
        CONSTRAINT unique_datastream_link UNIQUE(thing_id, datastream_name)
    );

    -- 2. Handle sms_device_property
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'sms_device_property') THEN
        DROP MATERIALIZED VIEW public.sms_device_property;
    END IF;

    CREATE TABLE IF NOT EXISTS public.sms_device_property (
        id SERIAL PRIMARY KEY,
        device_id INTEGER,
        property_name VARCHAR(256) NOT NULL,
        property_uri VARCHAR(256),
        label VARCHAR(256),
        unit_name VARCHAR(256),
        unit_uri VARCHAR(256)
    );

    -- 3. Handle sms_device_mount_action
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'sms_device_mount_action') THEN
        DROP MATERIALIZED VIEW public.sms_device_mount_action;
    END IF;

    CREATE TABLE IF NOT EXISTS public.sms_device_mount_action (
        id SERIAL PRIMARY KEY,
        configuration_id INTEGER,
        device_id INTEGER,
        begin_date TIMESTAMP WITH TIME ZONE NOT NULL,
        end_date TIMESTAMP WITH TIME ZONE,
        label VARCHAR(256)
    );

END $$;

