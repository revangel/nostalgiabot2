import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import Config, DevelopmentConfig

from nb2 import api, db
from nb2.slackbot import SlackBot


db = SQLAlchemy()
migrate = Migrate()
bot = SlackBot(token=os.environ['SLACK_BOT_TOKEN'])


def create_app(config=Config):
    """Create and configure an instance of Nostalgiabot2"""

    app = Flask(__name__, instance_relative_config=True)

    # TODO:
    # Find a way to set this more dynamically
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(api.bp)

    signing_secret = os.environ['SLACK_SIGNING_SECRET']
    event_url = os.environ['SLACK_EVENTS_URL']
    bot.init_app(signing_secret, event_url, app)

    # This is somewhat of a hack so that the decorators that
    # register slack event handlers will be run after
    # initializing the SlackEventAdapter in the bot.
    from nb2 import slack_events

    return app


# Avoid circular dependencies by having this import here
from nb2 import models
