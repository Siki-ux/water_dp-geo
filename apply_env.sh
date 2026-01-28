#!/bin/bash
# apply_env.sh
# This script copies the master.env to the .env files of all sub-projects.

SOURCE_FILE="master.env"
DESTINATIONS=(
    "water_dp-api/.env"
    "water_dp-geo/.env"
    "water_dp-hydro_portal/.env"
    "timeio/tsm-orchestration/.env"
)

if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: Could not find $SOURCE_FILE in the current directory."
    exit 1
fi

for DEST in "${DESTINATIONS[@]}"; do
    DEST_PATH="$(pwd)/$DEST"
    DEST_DIR=$(dirname "$DEST_PATH")
    
    if [ -d "$DEST_DIR" ]; then
        echo "Applying configuration to $DEST..."
        cp "$SOURCE_FILE" "$DEST_PATH"
    else
        echo "Warning: Directory $DEST_DIR does not exist, skipping."
    fi
done

echo -e "\nEnvironment configuration applied successfully!"
