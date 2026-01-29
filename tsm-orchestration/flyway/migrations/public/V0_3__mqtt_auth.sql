CREATE ROLE ${mqtt_auth_db_user} WITH LOGIN PASSWORD '${mqtt_auth_db_password}';
GRANT ${mqtt_auth_db_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS ${mqtt_auth_db_user} AUTHORIZATION ${mqtt_auth_db_user};
SET search_path TO ${mqtt_auth_db_user};
GRANT CONNECT ON DATABASE ${flyway:database} TO ${mqtt_auth_db_user};
ALTER ROLE ${mqtt_auth_db_user} SET search_path to ${mqtt_auth_db_user};
GRANT USAGE ON SCHEMA ${mqtt_auth_db_user} TO ${mqtt_auth_db_user};
GRANT ALL ON SCHEMA ${mqtt_auth_db_user} TO ${mqtt_auth_db_user};

CREATE TABLE "mqtt_user"
(
    "id"           bigserial    NOT NULL PRIMARY KEY,
    "project_uuid" uuid         NOT NULL,
    "thing_uuid"   uuid         NOT NULL UNIQUE,
    "username"     varchar(256) NOT NULL UNIQUE,
    "password"     varchar(256) NOT NULL,
    "db_schema"    varchar(256) NOT NULL,
    "description"  text         NULL,
    "properties"   jsonb        NULL,
    constraint mqtt_user_project_thing_unique
      unique (project_uuid, thing_uuid)
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ${mqtt_auth_db_user} TO ${mqtt_auth_db_user};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${mqtt_auth_db_user} TO ${mqtt_auth_db_user};