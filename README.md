# mediaserver

A Flask web application for browsing and playing music files

Development Status: Pre-Alpha

Features:
- Simple minimalist web interface, perfect for a party jukebox hosted on your home WiFi network
- Large (1000x1000px) album art display
- Continuous shuffle playback with filtering options
- Fast (tested with a library of 15,000+ music files)
- Versatile filtering and sorting via a common set of intuitive url parameters
- Comprehensive browsing options--browse by artist, album, genre, year, year range, and more
- Name That Tune--plays a song without displaying the info, but offering hints, challenging the user to name the artist/tune
- Direct download of music files via hyperlinks
- Accessible from mobile devices (tested in Chrome on Android)

[Screenshots](./screenshots/)

![Albums 600px Table Screenshot](./screenshots/Albums-600px-table.png)

Limitations:
- Doesn't work with some `.m4a` files (html5 audio element can't decode)
- Requires that music library be scanned with [mediascan](https://github.com/bretttolbert/mediascan) which outputs the [files.yaml](https://github.com/bretttolbert/mediascan/blob/main/files.yaml) file. This must be repeated to update the music library (e.g. add new files)
- Requires that music files be organized in the way that mediascan expects i.e. artist folders containing album folders with `cover.jpg` files
- Requires that music filenames not contain prohibited characters such as `+` (prevent by testing music library with [mediatest](https://github.com/bretttolbert/mediatest))
- Requires that your music library path begins with `/data/` (TODO: change this)

Coming soon:
- Play entire albums
- Playlists
- Back button to go back to previous track(s) in player
- Sort by modified time

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

## Player Filtered Continuous Shuffle Examples

###### Filter by year range

```bash
http://localhost:5000/player?minYear=1990&maxYear=2004
```

###### Filter by year range and genre(s)

```bash
http://localhost:5000/player?minYear=1960&maxYear=2024&genre=Industrial+Metal&genre=Punk&genre=Punk+Rock&genre=Heavy+Metal&genre=Hip+Hop&genre=Urbano&genre=Thrash+Metal&genre=Nu+Metal&genre=Rock+en+español&genre=Funk+Metal&genre=Hip-Hop+français
```

###### Filter by artist, album and title

```bash
http://localhost:5000/player?artist=Rush&album=Grace%20Under%20Pressure&title=The%20Body%20Electric
```
