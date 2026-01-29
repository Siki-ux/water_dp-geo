-- SPDX-FileCopyrightText: 2024
--
-- SMS Compatibility Schema
-- This file creates the tables required by TSM SQL views (like datastream_properties.sql)
-- so that Grafana dashboards work without errors even when thing-management-api is not used.

CREATE TABLE IF NOT EXISTS public.sms_device_property (
    id SERIAL PRIMARY KEY,
    property_name TEXT NOT NULL,
    unit_name TEXT,
    label TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS public.sms_device_mount_action (
    id SERIAL PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS public.sms_datastream_link (
    id SERIAL PRIMARY KEY,
    thing_id UUID NOT NULL,
    datastream_id INTEGER NOT NULL,
    device_property_id INTEGER REFERENCES public.sms_device_property(id),
    device_mount_action_id INTEGER REFERENCES public.sms_device_mount_action(id),
    CONSTRAINT unique_datastream_link UNIQUE(thing_id, datastream_id)
);

-- Grant access to PUBLIC so various TSM workers can read/write if needed
GRANT ALL ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;
