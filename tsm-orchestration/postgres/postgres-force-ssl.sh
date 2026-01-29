#!/usr/bin/env bash

if [ -f "/var/lib/postgresql/server.crt" ] && openssl x509 -in "/var/lib/postgresql/server.crt" -noout
  then
    sed -i "/^host all all all scram-sha-256/c\hostssl  all  all  all  scram-sha-256" /var/lib/postgresql/data/pgdata/pg_hba.conf
fi