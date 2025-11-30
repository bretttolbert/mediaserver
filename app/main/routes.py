from flask import (
    abort,
    current_app,
    render_template,
    request,
    Response,
    send_from_directory,
)
import random
from typing import List
from pathlib import Path

from mediascan import load_files_yaml, MediaFiles, MediaFile

from app.main import bp

from app.types.arg_types import args_dict_to_str
from app.utils.request_args_utils import get_request_args
from app.utils.media_files_utils import (
    filter_files,
    get_cover_path,
    get_genre_urls,
    get_albums,
    get_artist_counts,
    get_genre_counts,
    get_artist_urls,
)

MEDIASCAN_FILES_PATH = "../mediascan/out/files.yaml"

# !!! Important security note !!!
# Do not expose more than you need to with the music lib path below,
# Every file under this path will be exposed by the server!
# See the /getfile/ route.
MUSIC_LIB_PATH_PREFIX = "/data/"

files: MediaFiles = load_files_yaml(MEDIASCAN_FILES_PATH)


@bp.route("/")
def root() -> str:
    return render_template(
        "index.html",
    )


@bp.route("/tracks")
def tracks() -> str:
    global files
    args = get_request_args(request)
    current_app.logger.debug("tracks args=%s", args_dict_to_str(args))
    files_list: List[MediaFile] = filter_files(current_app, files, args)
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
    )


@bp.route("/player")
def player() -> str:
    return render_template("player.html")


@bp.route("/getfile/<path:path>")
def send_report(path: str) -> Response:
    if not path.startswith("/"):
        path = "/" + path
    path_prefix = MUSIC_LIB_PATH_PREFIX
    if not path_prefix.endswith("/"):
        path_prefix = path_prefix + "/"
    if path.startswith(path_prefix):
        path_without_prefix = path[len(path_prefix) :]
        current_app.logger.debug(
            "/getfile/ path=%s path_without_prefix=%s", path, path_without_prefix
        )
        return send_from_directory(MUSIC_LIB_PATH_PREFIX, path_without_prefix)
    else:
        current_app.logger.warning(
            "path (%s) doesn't start with MUSIC_LIB_PATH_PREFIX (%s), refusing to serve it",
            path,
            MUSIC_LIB_PATH_PREFIX,
        )
        abort(404)


@bp.route("/genres")
def genre_counts() -> str:
    sort: str = ""
    value = request.args.get("sort")
    if value:
        sort = value
    return render_template(
        "genres.html",
        genre_counts=get_genre_counts(files, sort=sort),
    )


@bp.route("/artists")
def artist_counts() -> str:
    genres: List[str] = request.args.getlist("genre")
    sort: str = ""
    value = request.args.get("sort")
    if value:
        sort = value
    return render_template(
        "artists.html",
        artist_counts=get_artist_counts(files, filter_genres=genres, sort=sort),
    )


@bp.route("/albums")
def albums() -> str:
    return render_template(
        "albums.html",
        albums=[
            album.to_tuple()
            for album in get_albums(current_app, files, get_request_args(request))
        ],
    )


@bp.route("/genres-cloud")
def genres_cloud() -> str:
    return render_template(
        "word-cloud.html",
        word_urls=get_genre_urls(files),
    )


@bp.route("/artists-cloud")
def artists_cloud() -> str:
    genres: List[str] = request.args.getlist("genre")
    return render_template(
        "word-cloud.html",
        word_urls=get_artist_urls(files, filter_genres=genres),
    )


@bp.route("/api/track")
def api_track():
    global files
    args = get_request_args(request)
    current_app.logger.debug("api/track args=%s", args_dict_to_str(args))
    files_list: List[MediaFile] = filter_files(current_app, files, args)
    if not len(files_list):
        abort(404)
    file = random.choice(files_list)
    cover_path = get_cover_path(file)
    return {
        "path": file.path,
        "cover_path": str(cover_path),
        "artist": file.artist,
        "album": file.album,
        "title": file.title,
        "genre": file.genre,
        "year": file.year,
    }
