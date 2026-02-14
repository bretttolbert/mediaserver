#!/bin/bash

cd mediascan
go run cmd/scantodb/main.go conf/conf.yaml out/mediascan.db
cd ..
