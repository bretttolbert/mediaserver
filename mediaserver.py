import sys
from flask import abort, Flask, render_template, request, send_from_directory  # type: ignore
import yaml
from datetime import datetime
import os.path
import random  # type: ignore
from typing import cast, Dict, List, Set, Tuple, Union
from urllib.parse import quote_plus  # type: ignore
from enum import StrEnum
from pathlib import Path

from mediascan import load_files_yaml, MediaFiles, MediaFile

app = Flask(__name__)  # type: ignore
app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)  # type: ignore
app.jinja_env.filters["make_list"] = lambda s: list(s)  # type: ignore
app.jinja_env.globals["PRESENT_YEAR"] = datetime.now().year  # type: ignore


MEDIASCAN_FILES_PATH = "../mediascan/out/files.yaml"

files: MediaFiles = load_files_yaml(MEDIASCAN_FILES_PATH)


class ArgType(StrEnum):
    pass


class ArgTypeScalarInt(ArgType):
    MinYear = "minYear"
    MaxYear = "maxYear"


class ArgTypeScalarEnum(ArgType):
    Sort = "sort"


class ArgTypeScalar:
    Int = ArgTypeScalarInt
    Enum = ArgTypeScalarEnum


class ArgTypeListStr(ArgType):
    Genre = "genre"
    Artist = "artist"
    AlbumArtist = "albumartist"
    Album = "album"
    Title = "title"
    Year = "year"


class ArgTypeList:
    Str = ArgTypeListStr


class ArgTypes:
    List = ArgTypeList
    Scalar = ArgTypeScalar


class ArgTypeUtil:
    @classmethod
    def is_scalar(cls, arg_type: ArgType) -> bool:
        return arg_type in (
            ArgTypes.Scalar.Int.MinYear,
            ArgTypes.Scalar.Int.MaxYear,
            ArgTypes.Scalar.Enum.Sort,
        )

    @classmethod
    def is_integer(cls, arg_type: ArgType) -> bool:
        return arg_type in (
            ArgTypes.Scalar.Int.MinYear,
            ArgTypes.Scalar.Int.MaxYear,
        )


ArgValueScalarInt = int
ArgValueListStr = List[str]


class ArgValueScalarEnumSort(StrEnum):
    Name = "name"
    Count = "count"
    Year = "year"
    Artist = "artist"
    Album = "album"


class ArgValuesScalarEnum:
    Sort = ArgValueScalarEnumSort


class ArgValuesScalar:
    Enum = ArgValuesScalarEnum


class ArgValues:
    Scalar = ArgValuesScalar


ArgValue = Union[ArgValueScalarInt, ArgValueListStr, ArgValueScalarEnumSort]
ArgsDict = Dict[ArgType, ArgValue]


REQUEST_ARG_TYPES = [
    ArgTypes.List.Str.Genre,
    ArgTypes.List.Str.Artist,
    ArgTypes.List.Str.AlbumArtist,
    ArgTypes.List.Str.Album,
    ArgTypes.List.Str.Title,
    ArgTypes.List.Str.Year,
    ArgTypes.Scalar.Int.MinYear,
    ArgTypes.Scalar.Int.MaxYear,
    ArgTypes.Scalar.Enum.Sort,
]


def get_request_args(
    arg_types: List[ArgType] = REQUEST_ARG_TYPES,
) -> ArgsDict:
    ret: ArgsDict = {}
    for arg_type in arg_types:
        if ArgTypeUtil.is_scalar(arg_type):
            value = request.args.get(str(arg_type))
            if value:
                if ArgTypeUtil.is_integer(arg_type):
                    ret[arg_type] = int(value)
                else:
                    # must be enum type, and there's only one currently
                    ret[arg_type] = ArgValues.Scalar.Enum.Sort(value)
        else:
            value = request.args.getlist(str(arg_type))
            if value:
                ret[arg_type] = value
    return ret


def filter_files(files: MediaFiles, args: ArgsDict) -> List[MediaFile]:
    ret: List[MediaFile] = []
    for f in files.files:
        # ArgTypeScalarInt:
        arg_type = ArgTypes.Scalar.Int.MinYear
        if arg_type in args:
            arg_value = cast(ArgValueScalarInt, args[arg_type])
            if arg_value and f.year < arg_value:
                continue
        arg_type = ArgTypes.Scalar.Int.MaxYear
        if arg_type in args:
            arg_value = cast(ArgValueScalarInt, args[arg_type])
            if arg_value and f.year > arg_value:
                continue
        # ArgTypeListStr:
        skip_file = False
        arg_type_list_file_value_map: Dict[ArgType, str] = {
            ArgTypes.List.Str.Artist: f.artist,
            ArgTypes.List.Str.AlbumArtist: f.albumartist,
            ArgTypes.List.Str.Album: f.album,
            ArgTypes.List.Str.Genre: f.genre,
            ArgTypes.List.Str.Title: f.title,
            ArgTypes.List.Str.Year: str(f.year),
        }
        for arg_type, file_value in arg_type_list_file_value_map.items():
            if arg_type in args:
                arg_value_list = cast(ArgValueListStr, args[arg_type])
                if len(arg_value_list) and file_value not in arg_value_list:
                    skip_file = True
                    break
        if not skip_file:
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
    if sort == ArgValues.Scalar.Enum.Sort.Name:
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


def get_cover_path(file: MediaFile) -> Path:
    rel_path = Path(file.path.replace(os.path.basename(file.path), ""))
    return rel_path / "cover.jpg"


# Tuple of [Artist, Album, Year, CoverPath]
AlbumInfoTuple = Tuple[str, str, int, str]


class AlbumInfo:
    def __init__(self, artist: str, album: str, year: int, cover_path: Path):
        self.artist = artist
        self.album = album
        self.year = year
        self.cover_path = cover_path

    def to_tuple(self) -> AlbumInfoTuple:
        return (self.artist, self.album, self.year, str(self.cover_path))


def get_albums(
    files: MediaFiles,
    args: ArgsDict,
) -> List[AlbumInfo]:
    """Returns a list of [Artist, Album, Year, CoverPath]"""
    ret: Set[AlbumInfo] = set()  # type: ignore
    files_filtered = filter_files(files, args)
    for f in files_filtered:
        # try to go with albumartist first, in order to better group files
        # in the same album together, but fallback to artist as key if
        # albumartist is not set
        artist = f.albumartist
        if not len(artist):
            artist = f.artist
        ret.add(AlbumInfo(artist, f.album, f.year, get_cover_path(f)))
    sort = ArgValues.Scalar.Enum.Sort.Year
    if ArgTypes.Scalar.Enum.Sort in args:
        sort = args[ArgTypes.Scalar.Enum.Sort]

    if sort == ArgValues.Scalar.Enum.Sort.Artist:
        return sorted(ret, key=lambda album: album.artist)
    if sort == ArgValues.Scalar.Enum.Sort.Album:
        return sorted(ret, key=lambda album: album.album)
    else:  # default: sort by year (descending)
        return sorted(ret, key=lambda album: album.year, reverse=True)


@app.route("/")  # type: ignore
def root() -> None:
    return render_template(
        "index.html",
    )  # type: ignore


@app.route("/tracks")  # type: ignore
def tracks() -> None:
    global files
    files_list: List[MediaFile] = filter_files(files, get_request_args())  # type: ignore
    cover_path: Path = Path()
    if len(files_list):
        cover_path = get_cover_path(files_list[0])
    return render_template(
        "tracks.html",
        files=sorted(
            files_list,
            key=lambda x: x.year,
            reverse=True,
        ),
        cover_path=str(cover_path),
    )  # type: ignore


@app.route("/player")  # type: ignore
def player() -> None:
    return render_template("player.html")  # type: ignore


@app.route("/data/<path:path>")  # type: ignore
def send_report(path: str) -> None:
    return send_from_directory("/data/", path)  # type: ignore


@app.route("/genres")  # type: ignore
def genre_counts() -> None:
    sort: str = ""
    value = request.args.get("sort")
    if value:
        sort = value
    return render_template(
        "genres.html",
        genre_counts=get_genre_counts(files, sort=sort),  # type: ignore
    )  # type: ignore


@app.route("/artists")  # type: ignore
def artist_counts() -> None:
    genres: List[str] = request.args.getlist("genre")  # type: ignore
    sort: str = ""
    value = request.args.get("sort")
    if value:
        sort = value
    return render_template(
        "artists.html",
        artist_counts=get_artist_counts(files, filter_genres=genres, sort=sort),  # type: ignore
    )  # type: ignore


@app.route("/albums")  # type: ignore
def albums() -> None:
    return render_template(
        "albums.html",
        albums=[album.to_tuple() for album in get_albums(files, get_request_args())],
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
    files_list: List[MediaFile] = filter_files(files, get_request_args())  # type: ignore
    if not len(files_list):
        abort(404)
    file = random.choice(files_list)
    cover_path = get_cover_path(file)  # type: ignore
    return {
        "path": file.path,
        "cover_path": str(cover_path),
        "artist": file.artist,
        "album": file.album,
        "title": file.title,
        "genre": file.genre,
        "year": file.year,
    }  # type: ignore
