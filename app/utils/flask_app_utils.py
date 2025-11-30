from datetime import datetime
from urllib.parse import quote_plus
from flask import Flask


def configure_flask_app(app: Flask):
    app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)
    app.jinja_env.filters["make_list"] = lambda s: list(s)
    app.jinja_env.globals["PRESENT_YEAR"] = datetime.now().year
    return app
