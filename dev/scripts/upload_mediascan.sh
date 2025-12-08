#!/bin/bash

rsync -ahvP mediascan/ root@$BT_DROPLET_IP:/var/www/mediax/mediascan/ --delete 

