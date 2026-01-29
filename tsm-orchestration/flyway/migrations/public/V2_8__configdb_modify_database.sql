SET search_path TO config_db;

alter table database
add column url varchar(200) null,
add column ro_url varchar(200) null;

