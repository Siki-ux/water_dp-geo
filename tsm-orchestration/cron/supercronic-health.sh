#!/bin/bash

# Loop through all commands of all processes in /proc
for cmd in /proc/[0-9]*/cmdline; do
  # Check the command line for the supercronic process
  tr '\0' ' ' < $cmd | grep -q "supercronic -inotify -split-logs" && echo "Supercronic is running." && exit 0
done
echo "Supercronic is not running."
exit 1