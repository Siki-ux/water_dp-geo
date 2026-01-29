-- Purpose: Create permanent local tables with sms_ prefix for TSM compatibility.
-- This ensures that views like datastream_properties.sql work even without a foreign SMS database.

CREATE TABLE IF NOT EXISTS public.sms_device_property (
    id SERIAL PRIMARY KEY,
    device_id INTEGER,
    property_name VARCHAR(256) NOT NULL,
    property_uri VARCHAR(256),
    label VARCHAR(256),
    unit_name VARCHAR(256),
    unit_uri VARCHAR(256),
    resolution DOUBLE PRECISION,
    resolution_unit_name VARCHAR(256),
    resolution_unit_uri VARCHAR(256),
    accuracy DOUBLE PRECISION,
    measuring_range_min DOUBLE PRECISION,
    measuring_range_max DOUBLE PRECISION,
    aggregation_type_name VARCHAR(256),
    aggregation_type_uri VARCHAR(256),
    accuracy_unit_name VARCHAR(256),
    accuracy_unit_uri VARCHAR(256)
);

CREATE TABLE IF NOT EXISTS public.sms_device_mount_action (
    id SERIAL PRIMARY KEY,
    configuration_id INTEGER,
    device_id INTEGER,
    offset_x DOUBLE PRECISION,
    offset_y DOUBLE PRECISION,
    offset_z DOUBLE PRECISION,
    begin_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    begin_description TEXT,
    label VARCHAR(256)
);

CREATE TABLE IF NOT EXISTS public.sms_datastream_link (
    id SERIAL PRIMARY KEY,
    thing_id UUID,
    device_property_id INTEGER REFERENCES public.sms_device_property(id),
    device_mount_action_id INTEGER REFERENCES public.sms_device_mount_action(id),
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


-- Grant access to PUBLIC
GRANT SELECT, INSERT, UPDATE, DELETE ON public.sms_device_property TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.sms_device_mount_action TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.sms_datastream_link TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;
