from typing import cast
from flask import current_app, Flask

from mediascan import MediaFiles, Artists

from app.types.config.mediaserver_config import MediaServerConfig


def get_config(app: Flask) -> MediaServerConfig:
    return cast(MediaServerConfig, current_app.config["MEDIASERVER_CONFIG"])


def get_mediascan_files(app: Flask) -> MediaFiles:
    return cast(MediaFiles, current_app.config["MEDIASCAN_FILES"])


def get_mediascan_artists(app: Flask) -> Artists:
    return cast(Artists, current_app.config["MEDIASCAN_ARTISTS"])
