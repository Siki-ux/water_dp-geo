SET search_path TO config_db;

alter table thing add column description varchar(200) null;

