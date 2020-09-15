import logging
import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import DevelopmentConfig
from nb2.bot.slackbot import SlackBot

db = SQLAlchemy()
migrate = Migrate()
bot = SlackBot()


def create_app(config=DevelopmentConfig):
    """Create and configure an instance of Nostalgiabot2"""

    app = Flask(__name__, instance_relative_config=True)

    # TODO:
    # Find a way to set these more dynamically
    app.config.from_object(config)
    app.logger.setLevel(logging.INFO)

    db.init_app(app)
    migrate.init_app(app, db)

    from nb2.management import commands

    app.register_blueprint(commands.bp)

    from nb2 import api

    app.register_blueprint(api.bp)

    token = os.environ["SLACK_BOT_TOKEN"]
    signing_secret = os.environ["SLACK_SIGNING_SECRET"]
    event_url = os.environ["SLACK_EVENTS_URL"]
    bot.init_app(token, signing_secret, event_url, app)

    # This is somewhat of a hack so that the decorators that
    # register slack event handlers will be run after
    # initializing the SlackEventAdapter in the bot.
    # from nb2.bot import slack_events
    from nb2.bot import slack_events  # noqa
    from nb2.models import Person, Quote

    @app.shell_context_processor
    def make_shell_context():
        """
        Automatically import commonly used models when starting
        the Flask shell
        """
        return {"bot": bot, "db": db, "Person": Person, "Quote": Quote}

    return app
