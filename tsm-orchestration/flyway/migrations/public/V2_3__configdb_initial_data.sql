INSERT INTO config_db.ingest_type (name)
VALUES ('sftp'::varchar(200)),
       ('mqtt'::varchar(200)),
       ('extsftp'::varchar(200)),
       ('extapi'::varchar(200));

INSERT INTO config_db.file_parser_type (name)
VALUES ('csvparser'::varchar(200));

INSERT INTO config_db.mqtt_device_type (name)
VALUES ('campbell_cr6'::varchar(200)),
       ('brightsky_dwd_api'::varchar(200)),
       ('ydoc_ml417'::varchar(200)),
       ('sine_dummy'::varchar(200));

INSERT INTO config_db.ext_api_type (name)
VALUES ('ttn'::varchar(200)),
       ('dwd'::varchar(200)),
       ('nm'::varchar(200));
