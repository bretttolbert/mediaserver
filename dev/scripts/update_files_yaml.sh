#!/bin/bash

cd mediascan
go run cmd/scanfiles/main.go conf/conf.yaml out/files.yaml
cd ..
