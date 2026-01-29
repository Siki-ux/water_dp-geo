ALTER TABLE mqtt_ingest ALTER COLUMN uri DROP NOT NULL;

ALTER TABLE thing ADD CONSTRAINT uuid_uniq UNIQUE (uuid);

ALTER TABLE rawdatastorage ALTER COLUMN fileserver_uri DROP NOT NULL;

INSERT INTO external_api_type (name)
VALUES ('uba'::varchar(200)),
       ('tsystems'::varchar(200));

INSERT INTO mqtt_device_type (name)
VALUES ('chirpstack_generic'::varchar(200));
