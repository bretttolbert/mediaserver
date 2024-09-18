# mediaserver

A Flask web application for browsing local music files

Features:
- Simple minimalist web interface, perfect for a party jukebox hosted on your home WiFi network
- Large (1000x1000px) album art display
- Fast (tested with a library of 15,000+ music files)
- Versatile filtering and sorting via a common set of intuitive url parameters
- Comprehensive browsing options--browse by artist, album, genre, year, year range, and more
- Name That Tune--plays a song without displaying the info, but offering hints, challenging the user to name the artist/tune
- Direct download of music files via hyperlinks
- Accessible from mobile devices (tested in Chrome on Android)

[Screenshots](./screenshots/)

Limitations:
- Requires that music library be scanned with [mediascan](https://github.com/bretttolbert/mediascan) which outputs the [files.yaml](https://github.com/bretttolbert/mediascan/blob/main/files.yaml) file. This must be repeated to update the music library (e.g. add new files)
- Requires that music files be organized in the way that mediascan expects i.e. artist folders containing album folders with `cover.jpg` files
- Requires that music filenames not contain prohibited characters such as `+` (prevent by testing music library with [mediatest](https://github.com/bretttolbert/mediatest))

Coming soon:
- Continuous shuffle
- Play entire albums
- Playlists

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
