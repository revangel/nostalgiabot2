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

def create_socket_mode(bot):
    # Add a new listener to receive messages from Slack
    # You can add more listeners like this
    print(bot.client.socket_mode_request_listeners)
    bot.client.socket_mode_request_listeners.append(slack_events.process)
    print(bot.client.socket_mode_request_listeners)
    # Establish a WebSocket connection to the Socket Mode servers
    out = bot.client.connect()
    print(out)
# Just not to stop this process
    from threading import Event
    Event().wait()