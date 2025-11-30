from flask import Flask

from app.utils.flask_app_utils import configure_flask_app


def create_app():
    app = Flask(__name__)
    app = configure_flask_app(app)
    from app.main import bp as main_bp

    app.register_blueprint(main_bp)
    return app
