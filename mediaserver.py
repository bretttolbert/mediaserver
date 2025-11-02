import sys
from flask import abort, Flask, render_template, request, send_from_directory  # type: ignore
import yaml
from datetime import datetime
import os.path
import random  # type: ignore
from typing import Dict, List, Set, Tuple
from urllib.parse import quote_plus  # type: ignore

from mediascan import load_files_yaml, MediaFiles, MediaFile

app = Flask(__name__)  # type: ignore
app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)  # type: ignore
app.jinja_env.filters["make_list"] = lambda s: list(s)  # type: ignore
app.jinja_env.globals["PRESENT_YEAR"] = datetime.now().year  # type: ignore


MEDIASCAN_FILES_PATH = "../mediascan/out/files.yaml"

files = load_files_yaml(MEDIASCAN_FILES_PATH)


def filter_files(
    files: MediaFiles,
    filter_artists: List[str],
    filter_albumartists: List[str],
    filter_albums: List[str],
    filter_genres: List[str],
    filter_titles: List[str],
    filter_years: List[str],
    min_year: int,
    max_year: int,
) -> List[MediaFile]:
    ret: List[MediaFile] = []
    for f in files.files:
        if len(filter_artists) and f.artist not in filter_artists:
            continue
        if len(filter_albumartists) and f.albumartist not in filter_albumartists:
            continue
        if len(filter_albums) and f.album not in filter_albums:
            continue
        if len(filter_genres) and f.genre not in filter_genres:
            continue
        if len(filter_titles) and f.title not in filter_titles:
            continue
        if len(filter_years) and str(f.year) not in filter_years:
            continue
        if min_year and f.year < int(min_year):
            continue
        if max_year and f.year > int(max_year):
            continue
        ret.append(f)
    return ret


def get_genres(files: MediaFiles) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    for f in files.files:
        ret.add(f.genre)
    return sorted(ret)


def get_genre_counts(files: MediaFiles, sort: str) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for f in files.files:
        if f.genre in ret:
            ret[f.genre] += 1
        else:
            ret[f.genre] = 1
    if sort == "name":
        return dict(sorted(ret.items(), key=lambda item: item[0], reverse=False))
    else:  # default sort: by count
        return dict(sorted(ret.items(), key=lambda item: item[1], reverse=True))


def get_artist_counts(
    files: MediaFiles, filter_genres: List[str], sort: str
) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for f in files.files:
        if len(filter_genres) < 1 or f.genre in filter_genres:
            if f.artist in ret:
                ret[f.artist] += 1
            else:
                ret[f.artist] = 1
    if sort == "name":
        return dict(sorted(ret.items(), key=lambda item: item[0], reverse=False))
    else:  # default sort: by count
        return dict(sorted(ret.items(), key=lambda item: item[1], reverse=True))


def get_genre_urls(files: MediaFiles) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    genres = get_genres(files)
    for g in genres:
        ret.append({"text": g, "url": f"/artists-cloud?genre={quote_plus(g)}"})
    return ret


def get_artists(files: MediaFiles, filter_genres: List[str]) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    for f in files.files:
        if len(filter_genres) < 1 or f.genre in filter_genres:
            ret.add(f.artist)
    return sorted(ret)


def get_artist_urls(
    files: MediaFiles, filter_genres: List[str]
) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    artists = get_artists(files, filter_genres)
    for a in artists:
        ret.append({"text": a, "url": f"/albums?artist={quote_plus(a)}"})
    return ret


def get_cover_path(file: MediaFile) -> str:
    return file.path.replace(os.path.basename(file.path), "") + "cover.jpg"


def get_albums(
    files: MediaFiles,
    filter_artists: List[str],
    filter_albumartists: List[str],
    filter_genres: List[str],
    filter_years: List[str],
    min_year: int,
    max_year: int,
    sort: str,
) -> List[Tuple[str, str, int, str]]:
    """Returns a list of [Artist, Album, Year, CoverPath]"""
    ret: Set[Tuple[str, str, int, str]] = set()  # type: ignore
    for f in files.files:
        if len(filter_artists) and f.artist not in filter_artists:
            continue
        if len(filter_albumartists) and f.albumartist not in filter_albumartists:
            continue
        if len(filter_genres) and f.genre not in filter_genres:
            continue
        if len(filter_years) and str(f.year) not in filter_years:
            continue
        if min_year and f.year < int(min_year):
            continue
        if max_year and f.year > int(max_year):
            continue
        artist = f.albumartist
        if not len(artist):
            artist = f.artist
        ret.add((artist, f.album, f.year, get_cover_path(f)))
    if sort == "artist":
        return sorted(ret, key=lambda item: item[0])
    if sort == "album":
        return sorted(ret, key=lambda item: item[1])
    else:  # default: sort by year (descending)
        return sorted(ret, key=lambda item: item[2], reverse=True)


@app.route("/")  # type: ignore
def root() -> None:
    return render_template(
        "index.html",
    )  # type: ignore


@app.route("/tracks")  # type: ignore
def tracks() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    artists: List[str] = request.args.getlist("artist")  # type: ignore
    albumartists: List[str] = request.args.getlist("albumartist")  # type: ignore
    albums: List[str] = request.args.getlist("album")  # type: ignore
    titles: List[str] = request.args.getlist("title")  # type: ignore
    years: List[str] = request.args.getlist("year")  # type: ignore
    min_year: int = request.args.get("minYear")  # type: ignore
    max_year: int = request.args.get("maxYear")  # type: ignore
    files_list: List[MediaFile] = filter_files(files, artists, albumartists, albums, genres, titles, years, min_year, max_year)  # type: ignore
    cover_path: str = ""
    if len(files_list):
        cover_path = get_cover_path(files_list[0])
    return render_template(
        "tracks.html",
        files=sorted(
            files_list,
            key=lambda x: x.year,
            reverse=True,
        ),
        cover_path=cover_path,
    )  # type: ignore


@app.route("/player")  # type: ignore
def player() -> None:
    return render_template("player.html")  # type: ignore


@app.route("/data/<path:path>")  # type: ignore
def send_report(path: str) -> None:
    return send_from_directory("/data/", path)  # type: ignore


@app.route("/genres")  # type: ignore
def genre_counts() -> None:
    sort: str = request.args.get("sort")  # type: ignore
    return render_template(
        "genres.html",
        genre_counts=get_genre_counts(files, sort=sort),  # type: ignore
    )  # type: ignore


@app.route("/artists")  # type: ignore
def artist_counts() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    sort: str = request.args.get("sort")  # type: ignore
    return render_template(
        "artists.html",
        artist_counts=get_artist_counts(files, filter_genres=genres, sort=sort),  # type: ignore
    )  # type: ignore


@app.route("/albums")  # type: ignore
def albums() -> None:
    artists: List[str] = request.args.getlist("artist")  # type: ignore
    albumartists: List[str] = request.args.getlist("albumartist")  # type: ignore
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    years: List[str] = request.args.getlist("year")  # type: ignore
    min_year: int = request.args.get("minYear")  # type: ignore
    max_year: int = request.args.get("maxYear")  # type: ignore
    sort: str = request.args.get("sort")  # type: ignore
    return render_template(
        "albums.html",
        albums=get_albums(
            files,
            filter_artists=artists,  # type: ignore
            filter_albumartists=albumartists,  # type: ignore
            filter_genres=genres,  # type: ignore
            filter_years=years,  # type: ignore
            min_year=min_year,  # type: ignore
            max_year=max_year,  # type: ignore
            sort=sort,  # type: ignore
        ),  # type: ignore
    )  # type: ignore


@app.route("/genres-cloud")  # type: ignore
def genres_cloud() -> None:
    return render_template(
        "word-cloud.html",
        word_urls=get_genre_urls(files),
    )  # type: ignore


@app.route("/artists-cloud")  # type: ignore
def artists_cloud() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    return render_template(
        "word-cloud.html",
        word_urls=get_artist_urls(files, filter_genres=genres),  # type: ignore
    )  # type: ignore


@app.route("/api/track")  # type: ignore
def api_track():  # type: ignore
    global files
    genres: List[str] = request.args.getlist("genre[]")  # type: ignore
    artists: List[str] = request.args.getlist("artist[]")  # type: ignore
    albumartists: List[str] = request.args.getlist("albumartist[]")  # type: ignore
    albums: List[str] = request.args.getlist("album[]")  # type: ignore
    titles: List[str] = request.args.getlist("title[]")  # type: ignore
    years: List[str] = request.args.getlist("year[]")  # type: ignore
    min_year: int = request.args.get("minYear")  # type: ignore
    max_year: int = request.args.get("maxYear")  # type: ignore
    files_list: List[MediaFile] = filter_files(files, artists, albumartists, albums, genres, titles, years, min_year, max_year)  # type: ignore
    if not len(files_list):
        abort(404)
    file = random.choice(files_list)
    cover_path = get_cover_path(file)  # type: ignore
    return {
        "path": file.path,
        "cover_path": cover_path,
        "artist": file.artist,
        "album": file.album,
        "title": file.title,
        "genre": file.genre,
        "year": file.year,
    }  # type: ignore
