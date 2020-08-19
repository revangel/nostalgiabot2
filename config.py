import os


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or ''

class DevelopmentConfig(Config):
    DEBUG = True
