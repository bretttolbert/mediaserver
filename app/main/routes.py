import os
import random
from typing import List
from pathlib import Path

from flask import (
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
    Response,
)

# from mediascan import MediaFile

from app.main import bp
from app.types.arg_types import args_dict_to_str
from app.utils.request_args_utils import get_request_args
from app.utils.media_files_utils import (
    get_files_list,
    get_cover_path,
    get_word_cloud_data_genres,
    get_albums,
    get_artist_counts,
    get_artist_country_code_counts,
    get_artist_region_code_counts,
    get_artist_language_code_counts,
    get_artist_city_counts,
    get_artist,
    get_genre_counts,
    get_tracks,
    get_word_cloud_data_artists,
    MediaFile,
)

# from app.utils.app_utils import get_config, get_mediascan_files, get_mediascan_artists
from app.utils.app_utils import (
    get_config,
    get_mediascan_db_artists,
    get_mediascan_db_files_artists_joined,
)


@bp.route("/")
def root() -> str:
    return render_template("albums_index.html", index_type="albums")


@bp.route("/tracks")
def tracks() -> str:
    global files
    config = get_config(current_app)
    args = get_request_args(request)
    current_app.logger.debug("tracks args=%s", args_dict_to_str(args))
    tracks: List[MediaFile] = get_tracks(
        current_app, get_mediascan_db_files_artists_joined(current_app), get_mediascan_db_artists(current_app), args
    )
    cover_path: Path = Path()
    if len(tracks):
        cover_path = get_cover_path(config, tracks[0])
    return render_template(
        "tracks.html",
        files=tracks,
        cover_path=str(cover_path),
    )


@bp.route("/tracks/index")
def tracks_index() -> str:
    return render_template("tracks_index.html")


from app.types.arg_types import (
    ArgsDict,
)


@bp.route("/player")
def player() -> str:
    kwargs = {}
    args: ArgsDict = get_request_args(request)
    for k, v in args.items():
        kwargs[k] = v
    return render_template("player.html", **kwargs)


@bp.route("/player/index")
def player_index() -> str:
    return render_template("player_index.html")


@bp.route("/name-that-tune/index")
def name_that_tune_index() -> str:
    return render_template("player_hints_index.html")


@bp.route("/getfile/<path:path>")
def getfile(path: str) -> Response:
    config = get_config(current_app)

    # path_prefix = /var/www/html/Covers/
    # path = /var/www/html/Covers/MusicOther/Johnny Cash/With His Hot and Blue Guitar [1957]/cover.jpg
    # path_without_prefix = MusicOther/Johnny Cash/With His Hot and Blue Guitar [1957]/cover.jpg

    if not path.startswith("/"):
        path = "/" + path
    path_prefix = config.playback_methods.local.media_path
    # if (
    #    path.startswith(config.album_covers_path)
    #    or config.album_covers_path != config.playback_methods.local.media_path
    # ):
    if path.startswith(config.album_covers_path):
        path_prefix = config.album_covers_path

    if not Path(path).exists():
        # if it's a jpg, try looking for webp instead of jpg
        # in case someone (me) converted the original jpgs to webp
        root, ext = os.path.splitext(path)
        if ext != ".jpg":
            current_app.logger.error('File not found (and not a jpg): "%s"', path)
            abort(404)
        oldpath = path
        path = root + ".webp"
        current_app.logger.warning(
            "Couldn't find file, trying different file extension:\noldpath=%s\nnewpath=%s",
            oldpath,
            path,
        )
    if not Path(path).exists():
        current_app.logger.error('File not found: "%s"', path)
        abort(404)
    else:
        current_app.logger.debug("File exists: %s", path)

    if not path_prefix.endswith("/"):
        path_prefix = path_prefix + "/"
    if path.startswith(path_prefix):
        path_without_prefix = path[len(path_prefix) :]
        current_app.logger.debug(
            '/getfile/ path="%s" path_prefix="%s" path_without_prefix="%s"',
            path,
            path_prefix,
            path_without_prefix,
        )
        current_app.logger.debug('send_from_directory("%s", "%s")', path_prefix, path_without_prefix)
        return send_from_directory(path_prefix, path_without_prefix)
    else:
        current_app.logger.warning(
            "path (%s) doesn't match expected media path prefix (%s), refusing to serve it",
            path,
            path_prefix,
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
        genre_counts=get_genre_counts(get_mediascan_db_files_artists_joined(current_app), sort=sort),
    )


@bp.route("/genre")
def genre() -> str:
    return render_template(
        "genre.html",
    )


@bp.route("/genres/index")
def genres_index() -> str:
    return render_template("genres_index.html", index_type="genres")


@bp.route("/artists")
def artists() -> str:
    return render_template(
        "artists.html",
        artist_counts=get_artist_counts(
            current_app,
            get_mediascan_db_files_artists_joined(current_app),
            get_mediascan_db_artists(current_app),
            get_request_args(request),
        ),
    )


@bp.route("/artist")
def artist() -> str:
    return render_template(
        "artist.html",
        artist=get_artist(
            current_app,
            get_mediascan_db_files_artists_joined(current_app),
            get_mediascan_db_artists(current_app),
            get_request_args(request),
        ),
    )


@bp.route("/artist-countries")
def artist_country_codes() -> str:
    return render_template(
        "artist_geo_codes.html",
        artist_query_count_info=get_artist_country_code_counts(
            current_app, get_mediascan_db_artists(current_app), get_request_args(request)
        ),
    )


@bp.route("/artist-regions")
def artist_region_codes() -> str:
    return render_template(
        "artist_geo_codes.html",
        artist_query_count_info=get_artist_region_code_counts(
            current_app, get_mediascan_db_artists(current_app), get_request_args(request)
        ),
    )


@bp.route("/artist-cities")
def artist_cities() -> str:
    return render_template(
        "artist_geo_codes.html",
        artist_query_count_info=get_artist_city_counts(
            current_app, get_mediascan_db_artists(current_app), get_request_args(request)
        ),
    )


@bp.route("/artist-languages")
def artist_languages() -> str:
    return render_template(
        "artist_geo_codes.html",
        artist_query_count_info=get_artist_language_code_counts(
            current_app, get_mediascan_db_artists(current_app), get_request_args(request)
        ),
    )


@bp.route("/artists/index")
def artists_index() -> str:
    return render_template("artists_index.html", index_type="artists")


@bp.route("/albums")
def albums() -> str:
    return render_template(
        "albums.html",
        albums=[
            album.to_tuple()
            for album in get_albums(
                current_app,
                get_mediascan_db_files_artists_joined(current_app),
                get_mediascan_db_artists(current_app),
                get_request_args(request),
            )
        ],
    )


@bp.route("/albums/index")
def albums_index() -> str:
    return render_template("albums_index.html", index_type="albums")


@bp.route("/genres-cloud")
def genres_cloud() -> str:
    return render_template(
        "word-cloud.html",
        word_cloud_data=get_word_cloud_data_genres(get_mediascan_db_files_artists_joined(current_app)),
        word_cloud_type="genre",
    )


@bp.route("/artists-cloud")
def artists_cloud() -> str:
    return render_template(
        "word-cloud.html",
        word_cloud_data=get_word_cloud_data_artists(
            current_app,
            get_mediascan_db_files_artists_joined(current_app),
            get_mediascan_db_artists(current_app),
            get_request_args(request),
        ),
        word_cloud_type="artist",
    )


@bp.route("/api/track")
def api_track():
    global files
    config = get_config(current_app)
    args = get_request_args(request)
    current_app.logger.debug("api/track args=%s", args_dict_to_str(args))
    files_list: List[MediaFile] = get_files_list(
        current_app, get_mediascan_db_files_artists_joined(current_app), get_mediascan_db_artists(current_app), args
    )
    if not len(files_list):
        abort(404)
    file = random.choice(files_list)
    cover_path = get_cover_path(config, file)
    return {
        "path": file.path,
        "cover_path": str(cover_path),
        "artist": file.artist,
        "album": file.album,
        "title": file.title,
        "genre": file.genre,
        "year": file.year,
        "countryCode": file.countryCode,
        "regionCode": file.regionCode,
        "city": file.city,
        "languageCode": file.languageCode,
    }
