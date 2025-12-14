#!/bin/bash

HOST=$MEDIASERVER_DROPLET_IP
DEST_USER=root
DEST_ROOT=/var/www/mediax
SVC=mediaserver
SOURCE=$SVC/
DEST=$DEST_USER@$HOST:$DEST_ROOT/$SVC/
echo "Uploading $SOURCE to $DEST"
rsync -ahvP $SOURCE $DEST --delete --exclude mediaserver_config.yaml --exclude '.git/' --exclude '.gitignore' --exclude '__pycache__/'
echo "Uploaded $SOURCE to $DEST"
