from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import Config, DevelopmentConfig

from nb2 import api, db

db = SQLAlchemy()
migrate = Migrate()


def create_app(config=Config):
    """Create and configure an instance of Nostalgiabot2"""

    app = Flask(__name__, instance_relative_config=True)

    # TODO:
    # Find a way to set this more dynamically
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(api.bp)

    return app

# Avoid circular dependencies by having this import here
from nb2 import models

