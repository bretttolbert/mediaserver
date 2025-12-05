from flask import Flask

from app.utils.flask_app_utils import configure_flask_app
from app.types.config.mediaserver_config import MediaServerConfig


def create_app(config: MediaServerConfig):
    app = Flask(__name__)
    app = configure_flask_app(app)
    app.config["MEDIASERVER_CONFIG"] = config
    app.debug = config.DEBUG
    from app.main import bp as main_bp

    app.register_blueprint(main_bp)
    return app
