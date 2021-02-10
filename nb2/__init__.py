import logging

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import DevelopmentConfig

db = SQLAlchemy()
migrate = Migrate()

# This import needs to come after db since the import chain
# in SlackBot eventually imports Person, which needs an
# instantiated db.
# TODO: Find a better way to handle circular imports?
from nb2.bot.slack_bot import SlackBot  # noqa

bot = SlackBot()


def create_app(config=DevelopmentConfig):
    """Create and configure an instance of Nostalgiabot2"""
    print('creating')
    app = Flask(__name__, instance_relative_config=True)

    # TODO:
    # Find a way to set these more dynamically
    app.config.from_object(config)
    app.logger.setLevel(logging.INFO)
    with app.app_context():
        db.init_app(app)
        migrate.init_app(app, db)

        from nb2 import api
        # from nb2.bot import slack_events
        from nb2.management import commands

        app.register_blueprint(api.bp)
        # app.register_blueprint(slack_events.bp)
        app.register_blueprint(commands.bp)
        bot.init_app(app.config.get("SLACK_BOT_TOKEN"), app.config.get("SLACK_APP_TOKEN"))

        from nb2.models import Person, Quote

        @app.shell_context_processor
        def make_shell_context():
            """
            Automatically import commonly used models when starting
            the Flask shell
            """
            return {"bot": bot, "db": db, "Person": Person, "Quote": Quote}

        return app
