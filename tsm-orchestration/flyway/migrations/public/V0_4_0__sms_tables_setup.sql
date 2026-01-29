-- Purpose: Create a foreign server pointing to the SMS database.
DO $$
BEGIN
    IF '${sms_access_type}' = 'db' THEN
        RAISE NOTICE 'Creating foreign server sms_db';
        CREATE SERVER sms_db
            FOREIGN DATA WRAPPER postgres_fdw
            OPTIONS (host '${sms_db_host}', dbname '${sms_db_db}', port '${sms_db_port}');
        CREATE USER MAPPING FOR ${flyway:user}
            SERVER sms_db
            OPTIONS (user '${sms_db_user}', password '${sms_db_password}');
    ELSE
        RAISE NOTICE 'Skipping creation of foreign server sms_db because sms_access_type is not db';
    END IF;
END $$;


-- Purpose: Create local tables to mock the sms database
create table public.contact
(
    id            serial primary key,
    given_name    varchar(256) not null,
    family_name   varchar(256) not null,
    website       varchar(1024),
    email         varchar(256) not null unique,
    active        boolean,
    created_at    timestamp with time zone,
    updated_at    timestamp with time zone,
    created_by_id integer,
    updated_by_id integer,
    organization  varchar(1024),
    orcid         varchar(32) unique
);


create table public.configuration
(
    created_at            timestamp with time zone,
    updated_at            timestamp with time zone,
    id                    serial not null primary key,
    start_date            timestamp with time zone,
    end_date              timestamp with time zone,
    created_by_id         integer,
    updated_by_id         integer,
    label                 varchar(256),
    status                varchar(256),
    cfg_permission_group  varchar,
    is_internal           boolean,
    is_public             boolean,
    update_description    varchar(256),
    archived              boolean,
    site_id               integer,
    project               varchar(256),
    description           text,
    persistent_identifier varchar(256)
        unique
);


create table public.configuration_contact_role
(
    role_name        varchar      not null,
    role_uri         varchar(256) not null,
    id               serial primary key,
    contact_id       integer      not null,
    configuration_id integer      not null
);


create table public.configuration_dynamic_location_begin_action
(
    created_at           timestamp with time zone,
    updated_at           timestamp with time zone,
    id                   serial primary key,
    configuration_id     integer not null,
    begin_date           timestamp with time zone not null,
    begin_description    text,
    begin_contact_id     integer not null,
    x_property_id        integer,
    y_property_id        integer,
    z_property_id        integer,
    epsg_code            varchar(256),
    elevation_datum_name varchar(256),
    elevation_datum_uri  varchar(256),
    created_by_id        integer,
    updated_by_id        integer,
    end_date             timestamp with time zone,
    end_description      text,
    end_contact_id       integer,
    label                varchar(256)
);


create table public.configuration_static_location_begin_action
(
    created_at           timestamp with time zone,
    updated_at           timestamp with time zone,
    id                   serial primary key,
    configuration_id     integer not null,
    begin_date           timestamp with time zone not null,
    begin_description    text,
    begin_contact_id     integer not null,
    x                    double precision,
    y                    double precision,
    z                    double precision,
    epsg_code            varchar(256),
    elevation_datum_name varchar(256),
    elevation_datum_uri  varchar(256),
    created_by_id        integer,
    updated_by_id        integer,
    end_date             timestamp with time zone,
    end_description      text,
    end_contact_id       integer,
    label                varchar(256)
);


create table public.device
(
    created_at            timestamp with time zone,
    updated_at            timestamp with time zone,
    id                    serial primary key,
    description           text,
    short_name            varchar(256) not null,
    long_name             varchar(256),
    serial_number         varchar(256),
    manufacturer_uri      varchar(256),
    manufacturer_name     varchar(256) not null,
    dual_use              boolean,
    model                 varchar(256),
    inventory_number      varchar(256),
    persistent_identifier varchar(256) unique,
    website               varchar(1024),
    device_type_uri       varchar(256),
    device_type_name      varchar(256),
    status_uri            varchar(256),
    status_name           varchar(256),
    created_by_id         integer,
    updated_by_id         integer,
    group_ids             character varying[],
    is_private            boolean,
    is_internal           boolean,
    is_public             boolean,
    update_description    varchar(256),
    archived              boolean,
    identifier_type       varchar(256),
    schema_version        varchar(256)
);


create table public.device_mount_action
(
    created_at         timestamp with time zone,
    updated_at         timestamp with time zone,
    id                 serial primary key,
    configuration_id   integer not null,
    device_id          integer not null,
    parent_platform_id integer,
    begin_date         timestamp with time zone not null,
    begin_description  text,
    begin_contact_id   integer not null,
    offset_x           double precision,
    offset_y           double precision,
    offset_z           double precision,
    created_by_id      integer,
    updated_by_id      integer,
    end_date           timestamp with time zone,
    end_description    text,
    end_contact_id     integer,
    label              varchar(256)
);


create table public.device_property
(
    id                    serial primary key,
    measuring_range_min   double precision,
    measuring_range_max   double precision,
    failure_value         double precision,
    accuracy              double precision,
    label                 varchar(256),
    unit_uri              varchar(256),
    unit_name             varchar(256),
    compartment_uri       varchar(256),
    compartment_name      varchar(256),
    property_uri          varchar(256),
    property_name         varchar(256) not null,
    sampling_media_uri    varchar(256),
    sampling_media_name   varchar(256),
    device_id             integer not null,
    resolution            double precision,
    resolution_unit_name  varchar(256),
    resolution_unit_uri   varchar(256),
    created_at            timestamp with time zone,
    updated_at            timestamp with time zone,
    created_by_id         integer,
    updated_by_id         integer,
    aggregation_type_uri  varchar(256),
    aggregation_type_name varchar(256),
    accuracy_unit_name    varchar(256),
    accuracy_unit_uri     varchar(256)

);


create table public.device_contact_role (
    id          serial primary key,
    role_uri    varchar(256) not null,
    role_name   varchar(256) not null,
    contact_id  integer not null,
    device_id   integer not null
);


create table public.datastream_link
(
    created_at             timestamp with time zone,
    updated_at             timestamp with time zone,
    id                     serial primary key,
    device_property_id     integer not null,
    device_mount_action_id integer not null,
    datasource_id          varchar(256) not null,
    thing_id               varchar(256) not null,
    datastream_id          varchar(256) not null,
    begin_date             timestamp with time zone,
    end_date               timestamp with time zone,
    created_by_id          integer,
    updated_by_id          integer,
    datasource_name        varchar(256),
    thing_name             varchar(256),
    datastream_name        varchar(256),
    license_uri            varchar(256),
    license_name           varchar(256),
    aggregation_period     double precision,
    tsm_endpoint_id        integer
);


-- Purpose: Create foreign tables for the SMS database.
DO $$
BEGIN
    IF '${sms_access_type}' = 'db' THEN
        RAISE NOTICE 'Creating foreign tables for sms';

        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_contact (
            id              integer not null,
            organization    varchar(1024),
            given_name      varchar(256),
            family_name     varchar(256),
            email           varchar(256),
            orcid           varchar(32)
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'contact');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration (
            id                      integer not null,
            label                   varchar(256),
            description             text,
            persistent_identifier   varchar(256),
            status                  varchar(256),
            project                 varchar(256),
            is_internal             boolean,
            is_public               boolean
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration_contact_role (
            id                  integer not null,
            configuration_id    integer not null,
            contact_id          integer not null,
            role_uri            varchar(256) not null,
            role_name           varchar(256) not null
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration_contact_role');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration_dynamic_location_begin_action (
            id                      integer not null,
            label                   varchar(256),
            configuration_id        integer not null,
            begin_date              timestamp with time zone not null,
            x_property_id           integer,
            y_property_id           integer,
            z_property_id           integer,
            epsg_code               varchar(256),
            elevation_datum_name    varchar(256),
            begin_description       text,
            end_date                timestamp with time zone
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration_dynamic_location_begin_action');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration_static_location_begin_action (
            id                  integer not null,
            x                   double precision,
            y                   double precision,
            z                   double precision,
            label               varchar(256),
            configuration_id    integer not null,
            begin_date          timestamp with time zone,
            begin_description   text,
            end_date            timestamp with time zone
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration_static_location_begin_action');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device (
            id                      integer not null,
            short_name              varchar(256),
            description             text,
            device_type_name        varchar(256),
            device_type_uri         varchar(256),
            manufacturer_name       varchar(256),
            manufacturer_uri        varchar(256),
            model                   varchar(256),
            serial_number           varchar(256),
            persistent_identifier   varchar(256),
            is_internal             boolean,
            is_public               boolean
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'device');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device_mount_action (
            id                  integer not null,
            configuration_id    integer not null,
            device_id           integer not null,
            offset_x            double precision,
            offset_y            double precision,
            offset_z            double precision,
            begin_date          timestamp with time zone not null,
            end_date            timestamp with time zone,
            begin_description   text,
            label               varchar(256)
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'device_mount_action');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device_property (
            id		                integer not null,
            device_id               integer not null,
            property_name           varchar(256) not null,
            property_uri            varchar(256),
            label		            varchar(256),
            unit_name	            varchar(256),
            unit_uri                varchar(256),
            resolution              double precision,
            resolution_unit_name    varchar(256),
            resolution_unit_uri     varchar(256),
            accuracy                double precision,
            measuring_range_min     double precision,
            measuring_range_max     double precision,
            aggregation_type_name   varchar(256),
            aggregation_type_uri    varchar(256),
            accuracy_unit_name      varchar(256),
            accuracy_unit_uri       varchar(256)

        )
            SERVER sms_db OPTIONS(schema_name 'public', table_name 'device_property');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device_contact_role (
            id          integer not null,
            role_uri    varchar(256) not null,
            role_name   varchar(256) not null,
            contact_id  integer not null,
            device_id   integer not null
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'device_contact_role');


        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_datastream_link (
            id                      integer not null,
            thing_id                uuid,
            device_property_id      integer not null,
            device_mount_action_id  integer not null,
            datasource_id           varchar(256),
            datastream_id           integer not null,
            begin_date              timestamp with time zone,
            end_date                timestamp with time zone,
            aggregation_period      double precision,
            license_uri             varchar(256),
            license_name            varchar(256)
        )
            SERVER sms_db OPTIONS (schema_name 'public', table_name 'datastream_link');

    ELSE
        RAISE NOTICE 'Skipping creation of foreign tables for sms because sms_access_type is not db';
    END IF;
END $$;
