CREATE TABLE ${flyway:defaultSchema}."schema_thing_mapping"(
    "schema"		VARCHAR(100) NOT NULL,
    "thing_uuid"	UUID NOT NULL,
    UNIQUE("schema", "thing_uuid"));
