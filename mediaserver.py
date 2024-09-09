from flask import Flask, render_template, send_from_directory  # type: ignore

import yaml
from dataclasses import dataclass

from dataclass_wizard import YAMLWizard  # type: ignore

from typing import List, Set, Tuple

from urllib.parse import quote_plus  # type: ignore

app = Flask(__name__)  # type: ignore
app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)  # type: ignore

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


def get_artists(data: Data) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    for f in data.mediafiles:
        ret.add(f.artist)
    return sorted(ret)


def get_albums(data: Data) -> List[Tuple[str, str, int]]:
    ret: Set[Tuple[str, str, int]] = set()  # type: ignore
    for f in data.mediafiles:
        ret.add((f.artist, f.album, f.year))
    return sorted(ret)


@app.route("/")  # type: ignore
def mediaserver() -> None:
    return render_template(
        "index.html",
        mediafiles=sorted(data.mediafiles, key=lambda x: x.year, reverse=True),
    )  # type: ignore


@app.route("/data/<path:path>")  # type: ignore
def send_report(path: str) -> None:
    return send_from_directory("/data/", path)  # type: ignore


@app.route("/genres")  # type: ignore
def genres() -> None:
    return render_template(
        "genres.html",
        genres=get_genres(data),
    )  # type: ignore


@app.route("/artists")  # type: ignore
def artists() -> None:
    return render_template(
        "artists.html",
        artists=get_artists(data),
    )  # type: ignore


@app.route("/albums")  # type: ignore
def albums() -> None:
    return render_template(
        "albums.html",
        albums=get_albums(data),
    )  # type: ignore


@app.route("/track")  # type: ignore
def track() -> None:
    return render_template(
        "track.html",
        mediafiles=sorted(data.mediafiles, key=lambda x: x.year, reverse=True),
    )  # type: ignore
