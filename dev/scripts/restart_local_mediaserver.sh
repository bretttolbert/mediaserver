#!/bin/bash

SVC=mediaserver
sudo systemctl stop $SVC && sleep 1 && systemctl start $SVC; echo 'Restarted $SVC'
echo 'Restarted mediaserver'
echo 'Done'
