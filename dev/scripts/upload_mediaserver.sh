#!/bin/bash

HOST=$MEDIASERVER_DROPLET_IP
DEST_USER=root
DEST_ROOT=/var/www/mediax
SVC=mediaserver
SOURCE=$SVC/
DEST=$DEST_USER@$HOST:$DEST_ROOT/$SVC/
echo "Uploading $SOURCE to $DEST"
# If first run, remove '--exclude 'app/templates/_css.html'
# I added that because I've put my analytics html there
rsync -ahvP $SOURCE $DEST --delete --exclude 'app/templates/_css.html' --exclude 'dev/' --exclude mediaserver_config.yaml --exclude '.git/' --exclude '.gitignore' --exclude '__pycache__/'
echo "Uploaded $SOURCE to $DEST"
