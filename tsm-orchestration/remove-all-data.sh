#!/usr/bin/env bash

rm -r data/minio/**/* data/minio/vol0/.minio.sys
rm -r data/postgres/data/*
rm data/mosquitto/**/*
rm -r data/grafana/*
rm -r data/tomcat/context/*
rm data/cron/*
exit 0
