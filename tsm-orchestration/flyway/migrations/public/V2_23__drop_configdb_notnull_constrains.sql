
alter table config_db.thing alter column mqtt_id drop not null;
alter table config_db.s3_store alter column file_parser_id drop not null;
