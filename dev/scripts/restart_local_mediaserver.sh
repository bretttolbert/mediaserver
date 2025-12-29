#!/bin/bash

SVC=mediaserver
systemctl stop $SVC && sleep 1 && systemctl start $SVC; echo "Restarted $SVC"
echo 'Restarted mediaserver'
echo 'Done'
