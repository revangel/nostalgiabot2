import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    SLACK_EVENTS_URL = os.environ.get("SLACK_EVENTS_URL") or ""
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or ""
    SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET") or ""
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN") or ""
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
        basedir, "app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///:memory:"
    SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET") or "x"
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN") or "x"
    SLACK_EVENTS_URL = os.environ.get("SLACK_EVENTS_URL") or "/x/"
