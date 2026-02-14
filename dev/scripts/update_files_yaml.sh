#!/bin/bash

cd mediascan
go run cmd/scanfilesyaml/main.go conf/conf.yaml out/files.yaml
cd ..
