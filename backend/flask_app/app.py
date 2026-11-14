from typing import Any

from flask import Flask

from flask_app.config import load_config
from flask_app.extensions import db, migrate


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config if config is not None else load_config())
    db.init_app(app)
    migrate.init_app(app, db)
    return app
