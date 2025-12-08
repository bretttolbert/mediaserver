#!/bin/bash

go run mediascan/mediascan/src/mediascan.go mediascan/conf/conf.yaml mediascan/out/files.yaml
python mediascan/scripts/copy_covers.py
python mediascan/scripts/convert_covers.py
rsync -ahvP /data/Covers/ root@$BT_DROPLET_IP:/var/www/html/Covers/ --delete 


