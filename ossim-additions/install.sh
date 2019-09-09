#!/bin/bash

SERVER_IP=""
SERVER_PORT="4343"

# Patch the menu

if [ "X$SERVER_IP" = "X" ]; then
    echo "The IP address must not be empty in install.sh!"
    exit 2
fi

echo "We will expect the logserver to be running at $SERVER_IP:$SERVER_PORT"

(cd / && patch -p0) < ./menu.patch
# Rewrite IP in index.php
sed -r -e "s|!SERVER!|$SERVER_IP|g" \
    -e "s|!PORT!|$SERVER_PORT|g" \
    -i ./logarchive/index.php
cp -r logarchive /usr/share/ossim/www/
echo "Running create_user.sh..."
./create_user.sh 
