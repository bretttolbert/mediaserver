from datetime import datetime
from flask import Flask


def configure_flask_app(app: Flask):
    app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)  # type: ignore
    app.jinja_env.filters["make_list"] = lambda s: list(s)  # type: ignore
    app.jinja_env.globals["PRESENT_YEAR"] = datetime.now().year  # type: ignore
    return app
