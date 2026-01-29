#!/bin/bash

MAX_ATTEMPTS="${RESTART_MAX_ATTEMPTS:-3}"
WINDOW_SECONDS="${RESTART_WINDOW_SECONDS:-10}"

if [[ $# -gt 0 ]]; then
  CMD="$@"
elif [[ -n "${CMD}" ]]; then
  CMD="${CMD}"
else
  echo "Error: No command provided."
  exit 1
fi

attempts=1
while [[ $attempts -le $MAX_ATTEMPTS ]]; do
  start=$(date +%s)
  echo "Attempt $((attempts)) of ${MAX_ATTEMPTS} to start container with command: $CMD"
  $CMD && exit 0
  ((attempts++))
  # Increment attempts and check time window
  end=$(date +%s)
  elapsed=$((end-start))

  # only count as failed attempt if within the window
  if [[ $elapsed -gt $WINDOW_SECONDS ]]; then
    # reset attempts and timer if outside the window
    echo "Failed attempt outside of $WINDOW_SECONDS seconds window. Resetting attempt counter."
    attempts=1
  fi
done

echo "Error: Command failed after $attempts attempts, each within the first $WINDOW_SECONDS seconds."
# We exit with the zero (success) status to prevent a restart of the container.
exit 0
