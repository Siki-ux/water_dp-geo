#!/bin/bash
cd "$(dirname "$0")/../.."

TEMP_ENV_FILE=$(mktemp)
TAG=${SSH_ORIGINAL_COMMAND}
git fetch origin
git show ${TAG}:.env.example > $TEMP_ENV_FILE

# compare the .env file with the .env.example file from the tag
# if it fails, rm TEMP_ENV_FILE and exit
# if it passes, rm TEMP_ENV_FILE and continue
# use venv with dotenv and click pre-installed
venv/bin/python3 compare_dotenv_files.py .env $TEMP_ENV_FILE
if [ $? -ne 0 ]; then
  rm $TEMP_ENV_FILE
  exit 1
fi
rm $TEMP_ENV_FILE

git checkout ${TAG}
rm remove-all-data.sh
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.override.prod.yml"
ENV_FILES="--env-file .env --env-file releases/release.env"
# ... otherwise deploy time.IO with the tag env file
docker compose $COMPOSE_FILES $ENV_FILES create --build
docker compose $COMPOSE_FILES $ENV_FILES up -d
sleep 10
docker compose $COMPOSE_FILES $ENV_FILES ps
# remove dangling docker images
docker rmi $(docker images -f dangling=true -q)
