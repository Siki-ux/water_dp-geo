CREATE ROLE ${monitoring_db_user} WITH LOGIN PASSWORD '${monitoring_db_password}';
GRANT ${monitoring_db_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS ${monitoring_db_user} AUTHORIZATION ${monitoring_db_user};
SET search_path TO ${monitoring_db_user};
GRANT CONNECT ON DATABASE ${flyway:database} TO ${monitoring_db_user};
ALTER ROLE ${monitoring_db_user} SET search_path to ${monitoring_db_user};
GRANT USAGE ON SCHEMA ${monitoring_db_user} TO ${monitoring_db_user};

SET SEARCH_PATH TO ${monitoring_db_user};

CREATE TABLE mqtt_broker (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    uptime INTERVAL,
    clients_inactive INTEGER,
    clients_disconnected INTEGER,
    clients_active INTEGER,
    clients_connected INTEGER,
    clients_maximum INTEGER,
    clients_expired INTEGER,
    clients_total INTEGER,
    load_messages_received_1min FLOAT,
    load_messages_received_5min FLOAT,
    load_messages_received_15min FLOAT,
    load_messages_sent_1min FLOAT,
    load_messages_sent_5min FLOAT,
    load_messages_sent_15min FLOAT,
    load_publish_received_1min FLOAT,
    load_publish_received_5min FLOAT,
    load_publish_received_15min FLOAT,
    load_publish_sent_1min FLOAT,
    load_publish_sent_5min FLOAT,
    load_publish_sent_15min FLOAT,
    load_publish_dropped_1min FLOAT,
    load_publish_dropped_5min FLOAT,
    load_publish_dropped_15min FLOAT,
    load_bytes_received_1min FLOAT,
    load_bytes_received_5min FLOAT,
    load_bytes_received_15min FLOAT,
    load_bytes_sent_1min FLOAT,
    load_bytes_sent_5min FLOAT,
    load_bytes_sent_15min FLOAT,
    load_sockets_1min FLOAT,
    load_sockets_5min FLOAT,
    load_sockets_15min FLOAT,
    load_connections_1min FLOAT,
    load_connections_5min FLOAT,
    load_connections_15min FLOAT,
    messages_stored INTEGER,
    messages_received INTEGER,
    messages_sent INTEGER,
    store_messages_count INTEGER,
    store_messages_bytes BIGINT,
    subscriptions_count INTEGER,
    shared_subscriptions_count INTEGER,
    retained_messages_count INTEGER,
    heap_current BIGINT,
    heap_maximum BIGINT,
    publish_messages_received INTEGER,
    publish_messages_sent INTEGER,
    publish_messages_dropped INTEGER,
    publish_bytes_received BIGINT,
    publish_bytes_sent BIGINT,
    bytes_received BIGINT,
    bytes_sent BIGINT
);

GRANT SELECT ON ALL TABLES IN SCHEMA ${monitoring_db_user} TO ${monitoring_db_user};
