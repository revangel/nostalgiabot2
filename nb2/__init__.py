from flask import Flask
from config import Config, DevelopmentConfig

from nb2 import api


def create_app(config=Config):
    """Create and configure an instance of Nostalgiabot2"""

    app = Flask(__name__, instance_relative_config=True)

    # TODO:
    # Find a way to set this more dynamically
    app.config.from_object(DevelopmentConfig)

    app.register_blueprint(api.bp)

    return app


