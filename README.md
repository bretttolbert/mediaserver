# mediaserver

A Flask web application for browsing media files, by artist, album, genre or year

## Dependencies

- [mediascan](https://github.com/bretttolbert/mediascan) A simple and fast Go (golang) command-line utility to recursively scan a directory for media files, extract metadata (including ID3v2 tags from both MP3 and M4A files), and save the output in a simple yaml format 

## Quick Start

```bash
flask --app mediaserver run
```
