from flask import (
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
    Response,
)
import random
from typing import List
from pathlib import Path

from mediascan import MediaFile

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

from app.utils.app_utils import get_config, get_media_files


@bp.route("/")
def root() -> str:
    return render_template(
        "albums_index.html",
    )


@bp.route("/tracks")
def tracks() -> str:
    global files
    config = get_config(current_app)
    args = get_request_args(request)
    current_app.logger.debug("tracks args=%s", args_dict_to_str(args))
    files_list: List[MediaFile] = filter_files(
        current_app, get_media_files(current_app), args
    )
    cover_path: Path = Path()
    if len(files_list):
        cover_path = get_cover_path(files_list[0], config)
    return render_template(
        "tracks.html",
        files=sorted(
            files_list,
            key=lambda x: x.year,
            reverse=True,
        ),
        cover_path=str(cover_path),
    )


@bp.route("/tracks/index")
def tracks_index() -> str:
    return render_template("tracks_index.html")


@bp.route("/player")
def player() -> str:
    return render_template(
        "player.html",
    )


@bp.route("/player/index")
def player_index() -> str:
    return render_template("player_index.html")


@bp.route("/name-that-tune/index")
def name_that_tune_index() -> str:
    return render_template("player_hints_index.html")


@bp.route("/getfile/<path:path>")
def send_report(path: str) -> Response:
    config = get_config(current_app)
    if not path.startswith("/"):
        path = "/" + path
    path_prefix = config.playback_methods.local.media_path
    if not path_prefix.endswith("/"):
        path_prefix = path_prefix + "/"
    if path.startswith(path_prefix):
        path_without_prefix = path[len(path_prefix) :]
        current_app.logger.debug(
            "/getfile/ path=%s path_without_prefix=%s", path, path_without_prefix
        )
        return send_from_directory(
            config.playback_methods.local.media_path, path_without_prefix
        )
    else:
        current_app.logger.warning(
            "path (%s) doesn't start with media_path (%s), refusing to serve it",
            path,
            config.playback_methods.local.media_path,
        )
        abort(404)


@bp.route("/genres")
def genres() -> str:
    sort: str = ""
    value = request.args.get("sort")
    if value:
        sort = value
    return render_template(
        "genres.html",
        genre_counts=get_genre_counts(get_media_files(current_app), sort=sort),
    )


@bp.route("/genres/index")
def genre_index() -> str:
    return render_template(
        "genres_index.html",
    )


@bp.route("/artists")
def artist_counts() -> str:
    sort: str = ""
    value = request.args.get("sort")
    if value:
        sort = value
    return render_template(
        "artists.html",
        artist_counts=get_artist_counts(
            current_app,
            get_media_files(current_app),
            get_request_args(request),
            sort=sort,
        ),
    )


@bp.route("/artists/index")
def artist_index() -> str:
    return render_template(
        "artists_index.html",
    )


@bp.route("/albums")
def albums() -> str:
    return render_template(
        "albums.html",
        albums=[
            album.to_tuple()
            for album in get_albums(
                current_app,
                get_media_files(current_app),
                get_request_args(request),
            )
        ],
    )


@bp.route("/albums/index")
def albums_index() -> str:
    return render_template(
        "albums_index.html",
    )


@bp.route("/genres-cloud")
def genres_cloud() -> str:
    return render_template(
        "word-cloud.html",
        word_urls=get_genre_urls(get_media_files(current_app)),
    )


@bp.route("/artists-cloud")
def artists_cloud() -> str:
    return render_template(
        "word-cloud.html",
        word_urls=get_artist_urls(
            current_app, get_media_files(current_app), get_request_args(request)
        ),
    )


@bp.route("/api/track")
def api_track():
    global files
    config = get_config(current_app)
    args = get_request_args(request)
    current_app.logger.debug("api/track args=%s", args_dict_to_str(args))
    files_list: List[MediaFile] = filter_files(
        current_app, get_media_files(current_app), args
    )
    if not len(files_list):
        abort(404)
    file = random.choice(files_list)
    cover_path = get_cover_path(file, config)
    return {
        "path": file.path,
        "cover_path": str(cover_path),
        "artist": file.artist,
        "album": file.album,
        "title": file.title,
        "genre": file.genre,
        "year": file.year,
    }
