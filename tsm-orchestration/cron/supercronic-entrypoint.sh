#!/bin/bash

set -e

update_crontab() {
  # check if crontab file is valid
  if supercronic -test /tmp/cron/crontab.txt; then
    cp /tmp/cron/crontab.txt /tmp/crontab.txt
    echo "Starting supercronic with crontab /tmp/crontab.txt"
  else
    echo "New crontab file is invalid. Not using it..."
  fi
}

if [ "$SETUP_SERVICE" == "true" ]; then
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - starting cron setup."
  # Monitor crontab.txt for changes and update crontab if they occur
  # run loop in background to start cron service
  # check mounted crontab file and copy to /tmp/crontab.txt if valid
  update_crontab
  # start supercronic in background and wait for changes in /tmp/crontab.txt
  supercronic -inotify -split-logs /tmp/crontab.txt &
  while true; do
    # wait for changes of mounted crontab file
    inotifywait -e modify /tmp/cron/crontab.txt
    # and update crontab if they are valid
    update_crontab
  done
else
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - skipping cron setup."
  echo "To start cron setup, set SETUP_SERVICE to 'true' in .env file."
fi