from flask import Flask, render_template, request, send_from_directory  # type: ignore

import yaml
from dataclasses import dataclass

from dataclass_wizard import YAMLWizard  # type: ignore
import os.path
import random  # type: ignore
from typing import Dict, List, Set, Tuple

from urllib.parse import quote_plus  # type: ignore

app = Flask(__name__)  # type: ignore
app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)  # type: ignore
app.jinja_env.filters["make_list"] = lambda s: list(s)  # type: ignore

MEDIASCAN_FILES_PATH = "../mediascan/files.yaml"


@dataclass
class Mediafile:
    """
    Mediafile dataclass

    """

    path: str
    size: int
    format: str
    title: str
    artist: str
    album: str
    genre: str
    year: int
    duration: int


@dataclass
class Data(YAMLWizard):  # type: ignore
    """
    Data dataclass

    """

    mediafiles: list[Mediafile]


def load_yaml_file(yaml_fname: str) -> Data:
    data = None
    with open(yaml_fname, "r") as stream:
        try:
            data = Data.from_yaml(stream)  # type: ignore
        except yaml.YAMLError as exc:
            print(exc)
    return data  # type: ignore


data = load_yaml_file(MEDIASCAN_FILES_PATH)


def get_genres(data: Data) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    for f in data.mediafiles:
        ret.add(f.genre)
    return sorted(ret)


def get_genre_counts(data: Data) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for f in data.mediafiles:
        if f.genre in ret:
            ret[f.genre] += 1
        else:
            ret[f.genre] = 1
    return dict(sorted(ret.items(), key=lambda item: item[1], reverse=True))


def get_artist_counts(data: Data) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for f in data.mediafiles:
        if f.artist in ret:
            ret[f.artist] += 1
        else:
            ret[f.artist] = 1
    return dict(sorted(ret.items(), key=lambda item: item[1], reverse=True))


def get_genre_urls(data: Data) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    genres = get_genres(data)
    for g in genres:
        ret.append({"text": g, "url": f"/artists-cloud?genre={quote_plus(g)}"})
    return ret


def get_artists(data: Data, filter_genres: List[str]) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    for f in data.mediafiles:
        if len(filter_genres) < 1 or f.genre in filter_genres:
            ret.add(f.artist)
    return sorted(ret)


def get_artist_urls(data: Data, filter_genres: List[str]) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    artists = get_artists(data, filter_genres)
    for a in artists:
        ret.append({"text": a, "url": f"/albums?artist={quote_plus(a)}"})
    return ret


def get_cover_path(media_file: Mediafile) -> str:
    return media_file.path.replace(os.path.basename(media_file.path), "") + "cover.jpg"


def get_albums(
    data: Data,
    filter_artists: List[str],
    filter_genres: List[str],
    filter_years: List[str],
    sort: str,
) -> List[Tuple[str, str, int, str]]:
    ret: Set[Tuple[str, str, int, str]] = set()  # type: ignore
    for f in data.mediafiles:
        if len(filter_artists) and f.artist not in filter_artists:
            continue
        if len(filter_genres) and f.genre not in filter_genres:
            continue
        if len(filter_years) and str(f.year) not in filter_years:
            continue
        ret.add((f.artist, f.album, f.year, get_cover_path(f)))
    if sort == "artist":
        return sorted(ret, key=lambda item: item[0])
    if sort == "album":
        return sorted(ret, key=lambda item: item[1])
    else:  # default: sort by year (descending)
        return sorted(ret, key=lambda item: item[2], reverse=True)


def get_files(
    data: Data,
    filter_artists: List[str],
    filter_albums: List[str],
    filter_genres: List[str],
    filter_titles: List[str],
    filter_years: List[str],
    min_year: int,
    max_year: int,
) -> List[Mediafile]:
    ret: List[Mediafile] = []
    for f in data.mediafiles:
        if len(filter_artists) and f.artist not in filter_artists:
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


@app.route("/")  # type: ignore
def root() -> None:
    return render_template(
        "index.html",
    )  # type: ignore


@app.route("/tracks")  # type: ignore
def tracks() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    artists: List[str] = request.args.getlist("artist")  # type: ignore
    albums: List[str] = request.args.getlist("album")  # type: ignore
    titles: List[str] = request.args.getlist("title")  # type: ignore
    years: List[str] = request.args.getlist("year")  # type: ignore
    min_year: int = request.args.get("minYear")  # type: ignore
    max_year: int = request.args.get("maxYear")  # type: ignore
    files: List[Mediafile] = get_files(data, artists, albums, genres, titles, years, min_year, max_year)  # type: ignore
    cover_path: str = ""
    if len(files):
        cover_path = get_cover_path(files[0])
    return render_template(
        "tracks.html",
        files=sorted(
            files,
            key=lambda x: x.year,
            reverse=True,
        ),
        cover_path=cover_path,
    )  # type: ignore


@app.route("/name-that-tune")  # type: ignore
def name_that_tune() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    artists: List[str] = request.args.getlist("artist")  # type: ignore
    albums: List[str] = request.args.getlist("album")  # type: ignore
    titles: List[str] = request.args.getlist("title")  # type: ignore
    years: List[str] = request.args.getlist("year")  # type: ignore
    min_year: int = request.args.get("minYear")  # type: ignore
    max_year: int = request.args.get("maxYear")  # type: ignore
    files: List[Mediafile] = get_files(data, artists, albums, genres, titles, years, min_year, max_year)  # type: ignore
    return render_template(
        "name-that-tune.html",
        file=random.choice(files),  # type: ignore
    )  # type: ignore


@app.route("/player")  # type: ignore
def player() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    artists: List[str] = request.args.getlist("artist")  # type: ignore
    albums: List[str] = request.args.getlist("album")  # type: ignore
    titles: List[str] = request.args.getlist("title")  # type: ignore
    years: List[str] = request.args.getlist("year")  # type: ignore
    min_year: int = request.args.get("minYear")  # type: ignore
    max_year: int = request.args.get("maxYear")  # type: ignore
    files: List[Mediafile] = get_files(data, artists, albums, genres, titles, years, min_year, max_year)  # type: ignore
    return render_template(
        "player.html",
        file=random.choice(files),  # type: ignore
    )  # type: ignore


@app.route("/data/<path:path>")  # type: ignore
def send_report(path: str) -> None:
    return send_from_directory("/data/", path)  # type: ignore


@app.route("/genres-alpha")  # type: ignore
def genres_alpha() -> None:
    return render_template(
        "genres-alpha.html",
        genres=get_genres(data),
    )  # type: ignore


@app.route("/genre-counts")  # type: ignore
def genre_counts() -> None:
    return render_template(
        "genre-counts.html",
        genre_counts=get_genre_counts(data),
    )  # type: ignore


@app.route("/genres-cloud")  # type: ignore
def genres_cloud() -> None:
    return render_template(
        "word-cloud.html",
        word_urls=get_genre_urls(data),
    )  # type: ignore


@app.route("/artists-cloud")  # type: ignore
def artists_cloud() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    return render_template(
        "word-cloud.html",
        word_urls=get_artist_urls(data, filter_genres=genres),  # type: ignore
    )  # type: ignore


@app.route("/artist-counts")  # type: ignore
def artist_counts() -> None:
    return render_template(
        "artist-counts.html",
        artist_counts=get_artist_counts(data),
    )  # type: ignore


@app.route("/artists-alpha")  # type: ignore
def artists_alpha() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    return render_template(
        "artists-alpha.html",
        artists=get_artists(data, filter_genres=genres),  # type: ignore
    )  # type: ignore


@app.route("/albums")  # type: ignore
def albums() -> None:
    artists: List[str] = request.args.getlist("artist")  # type: ignore
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    years: List[str] = request.args.getlist("year")  # type: ignore
    sort: str = request.args.get("sort")  # type: ignore
    return render_template(
        "albums.html",
        albums=get_albums(data, filter_artists=artists, filter_genres=genres, filter_years=years, sort=sort),  # type: ignore
    )  # type: ignore
