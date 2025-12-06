from typing import Dict

from flask import Flask
import flask_jsglue

from mediascan import load_files_yaml

from app.types.config.mediaserver_config import MediaServerConfig

from datetime import datetime
from urllib.parse import quote_plus


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
    root_path = config.flask_config.root_path
    url_prefix = config.flask_config.url_prefix
    static_url_path = config.flask_config.static_url_path
    app = Flask(__name__, root_path=root_path, static_url_path=static_url_path)
    flask_jsglue.init(app, url_prefix)
    app.logger.debug("flask_config.root_path: %s", root_path)
    app.logger.debug("flask_config.url_prefix: %s", url_prefix)
    app.config["MEDIASERVER_CONFIG"] = config
    app.config["MEDIA_FILES"] = load_files_yaml(config.files_yaml_path)
    app.debug = config.flask_config.debug
    app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)
    app.jinja_env.filters["make_list"] = lambda s: list(s)
    app.jinja_env.filters["format_search_query_url"] = (
        lambda args: format_search_query_url(args, config)
    )
    app.jinja_env.globals["PRESENT_YEAR"] = datetime.now().year
    app.jinja_env.globals["PLAYBACK_METHOD_LOCAL_ENABLED"] = (
        config.playback_methods.local.enabled
    )

    app.jinja_env.globals["PLAYBACK_METHOD_YOUTUBE_ENABLED"] = (
        config.playback_methods.youtube.enabled
    )

    app.jinja_env.globals["SEARCH_QUERY_URL_FORMAT"] = (
        config.playback_methods.youtube.search_query_url_format
    )

    app.jinja_env.globals["AGE_VERIFICATION"] = config.age_verification

    from app.main import bp

    if url_prefix is None:
        app.register_blueprint(bp)
        app.jinja_env.globals["URL_PREFIX"] = ""
    else:
        app.register_blueprint(bp, url_prefix=url_prefix)
        app.jinja_env.globals["URL_PREFIX"] = url_prefix
    return app
