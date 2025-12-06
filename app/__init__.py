from typing import Dict
from flask import Flask

from mediascan import load_files_yaml

from app.types.config.mediaserver_config import MediaServerConfig

from datetime import datetime
from urllib.parse import quote_plus
from flask import Flask


def format_search_query_url(args: Dict[str, str], config: MediaServerConfig):
    artist = quote_plus(args["artist"])
    album = quote_plus(args["album"])
    title = quote_plus(args["title"])
    ret = config.playback_methods.youtube.search_query_url_format
    ret = ret.replace("{artist}", artist)
    ret = ret.replace("{album}", album)
    ret = ret.replace("{title}", title)
    return ret


def create_app(config: MediaServerConfig):
    app = Flask(__name__)
    app.config["MEDIASERVER_CONFIG"] = config
    app.config["MEDIA_FILES"] = load_files_yaml(config.files_yaml_path)
    app.debug = config.debug
    app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)
    app.jinja_env.filters["make_list"] = lambda s: list(s)
    app.jinja_env.filters["format_search_query_url"] = (
        lambda args: format_search_query_url(args, config)
    )
    app.jinja_env.globals["PRESENT_YEAR"] = datetime.now().year
    app.jinja_env.globals["PLAYBACK_METHOD_LOCAL_ENABLED"] = str(
        config.playback_methods.local.enabled
    ).lower()
    app.jinja_env.globals["PLAYBACK_METHOD_YOUTUBE_ENABLED"] = str(
        config.playback_methods.youtube.enabled
    ).lower()
    app.jinja_env.globals["SEARCH_QUERY_URL_FORMAT"] = (
        config.playback_methods.youtube.search_query_url_format
    )

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)
    return app
