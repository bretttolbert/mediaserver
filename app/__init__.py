from typing import Dict, Iterable, Optional
from datetime import datetime
from urllib.parse import quote_plus
from pathlib import Path
from flask import Flask
import flask_jsglue
import sqlite3
import pandas as pd

from mediascan import load_files_yaml, load_artists_yaml

from app.types.config.mediaserver_config import MediaServerConfig


class MediaScanDatabaseConnection:
    def __init__(self, mediascan_db_file_path: str):
        self._conn: sqlite3.Connection = sqlite3.connect(mediascan_db_file_path)
        # cur: sqlite3.Cursor = conn.cursor()
        # mediafiles_df = pd.read_sql_query("SELECT * FROM mediafile", conn)
        # artists_df = pd.read_sql_query("SELECT * FROM artist", conn)

    def get_conn(self):
        return self._conn


def format_search_query_url(args: Dict[str, str], config: MediaServerConfig):
    artist = quote_plus(args["artist"])
    album = quote_plus(args["album"])
    title = quote_plus(args["title"])
    ret = config.playback_methods.youtube.search_query_url_format
    ret = ret.replace("{artist}", artist)
    ret = ret.replace("{album}", album)
    ret = ret.replace("{title}", title)
    return ret


def format_results_string(l: Iterable, max_results: int):
    L = len(list(l))
    return f"{L:,}{'+' if L >= max_results else ''} {'result' if L == 1 else 'results'}"


def register_filters(app: Flask, config: MediaServerConfig):
    app.jinja_env.filters["result_or_results"] = lambda l: format_results_string(l, config.max_results)
    app.jinja_env.filters["result_or_results_album_covers"] = lambda l: format_results_string(
        l, config.max_results_album_covers
    )
    app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)
    app.jinja_env.filters["make_list"] = lambda s: list(s)
    app.jinja_env.filters["format_search_query_url"] = lambda args: format_search_query_url(args, config)


def set_globals(
    app: Flask,
    config: MediaServerConfig,
):
    app.jinja_env.globals["PRESENT_YEAR"] = datetime.now().year
    app.jinja_env.globals["PLAYBACK_METHOD_LOCAL_ENABLED"] = config.playback_methods.local.enabled

    app.jinja_env.globals["PLAYBACK_METHOD_YOUTUBE_ENABLED"] = config.playback_methods.youtube.enabled

    app.jinja_env.globals["SEARCH_QUERY_URL_FORMAT"] = config.playback_methods.youtube.search_query_url_format

    app.jinja_env.globals["AGE_VERIFICATION"] = config.age_verification

    app.jinja_env.globals["LIMIT_BANDWIDTH"] = config.limit_bandwidth


def register_blueprint(app: Flask, config: MediaServerConfig, url_prefix: Optional[str] = None):
    from app.main import bp

    if url_prefix is None:
        app.register_blueprint(bp)
        app.jinja_env.globals["URL_PREFIX"] = ""
    else:
        app.register_blueprint(bp, url_prefix=url_prefix)
        app.jinja_env.globals["URL_PREFIX"] = url_prefix


def create_app(config: MediaServerConfig):
    root_path = config.flask_config.root_path
    url_prefix = config.flask_config.url_prefix
    static_url_path = config.flask_config.static_url_path
    app = Flask(__name__, root_path=root_path, static_url_path=static_url_path)
    flask_jsglue.init(app, url_prefix)
    app.logger.debug("flask_config.root_path: %s", root_path)
    app.logger.debug("flask_config.url_prefix: %s", url_prefix)
    app.logger.debug("flask_config.static_url_path: %s", static_url_path)
    app.config["MEDIASERVER_CONFIG"] = config
    # app.config["MEDIASCAN_FILES"] = load_files_yaml(str(Path(config.mediascan_yaml_path).joinpath("files.yaml")))
    # app.config["MEDIASCAN_ARTISTS"] = load_artists_yaml(str(Path(config.mediascan_yaml_path).joinpath("artists.yaml")))
    db_conn = MediaScanDatabaseConnection(config.mediascan_database_file_path)
    app.config["MEDIASCAN_DB_CONN"] = db_conn
    app.config["MEDIASCAN_FILES_DF"] = pd.read_sql_query("SELECT * FROM mediafile", db_conn)
    app.config["MEDIASCAN_ARTISTS_DF"] = pd.read_sql_query("SELECT * FROM artists", db_conn)
    app.debug = config.flask_config.debug
    register_filters(app, config)
    set_globals(app, config)
    register_blueprint(app, config, url_prefix)
    return app
