# mediaserver

A Flask web application for browsing media files, by artist, album, genre or year

## Dependencies

- [mediascan](https://github.com/bretttolbert/mediascan) A simple and fast Go (golang) command-line utility to recursively scan a directory for media files, extract metadata (including ID3v2 tags from both MP3 and M4A files), and save the output in a simple yaml format 

## Quick Start

```bash
git clone git@github.com:bretttolbert/mediascan.git
cd mediascan
go run mediascan.go conf.yaml files.yaml
cd ..
git clone git@github.com:bretttolbert/mediaserver.git
cd mediaserver
flask --app mediaserver run --host=0.0.0.0
```
