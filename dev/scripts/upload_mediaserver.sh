#!/bin/bash

rsync -ahvP mediaserver/ root@$BT_DROPLET_IP:/var/www/mediax/mediaserver/ --delete \
    --exclude 'mediaserver_config.yaml'


