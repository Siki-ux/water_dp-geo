CREATE ROLE ${configdb_user} WITH LOGIN PASSWORD '${configdb_password}';
GRANT ${configdb_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS config_db AUTHORIZATION ${configdb_user};
GRANT CONNECT ON DATABASE ${flyway:database} TO ${configdb_user};
ALTER ROLE ${configdb_user} SET search_path TO config_db;
GRANT USAGE ON SCHEMA config_db TO ${configdb_user};
GRANT SELECT ON ALL TABLES IN SCHEMA config_db TO ${configdb_user};