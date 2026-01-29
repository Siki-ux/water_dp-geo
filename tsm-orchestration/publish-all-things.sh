#!/usr/bin/env bash
DIR_SCRIPT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker compose -f "${DIR_SCRIPT}/docker-compose.all-things-publisher.yml" run --rm  all-things-publisher publish_all_things.py
