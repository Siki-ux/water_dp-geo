SET search_path TO config_db;

alter table qaqc_test
add column name varchar(200) null,
add column streams jsonb null;

