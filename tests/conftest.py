import os

import pytest
from mixer.backend.flask import mixer

from nb2 import create_app
from nb2 import db as _db
from config import TestConfig


@pytest.fixture(scope="session")
def app(request):
    """Test session-wide test `Flask` application."""
    os.environ['SLACK_BOT_TOKEN'] = "x"
    os.environ['SLACK_SIGNING_SECRET'] = "x"
    os.environ['SLACK_EVENTS_URL'] = "/x/"

    app = create_app(TestConfig)

    return app


@pytest.fixture(autouse=True)
def _setup_app_context_for_test(request, app):
    """
    Given app is session-wide, sets up a app context per test to ensure that
    app and request stack is not shared between tests.
    """
    ctx = app.app_context()
    ctx.push()
    yield  # tests will run here
    ctx.pop()


@pytest.fixture(scope="session")
def client(app, request):
    return app.test_client()


@pytest.fixture(scope="session")
def db(app, request):
    """Returns session-wide initialized database"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope="function")
def session(app, db, request):
    """Creates a new database session for each test, rolling back changes afterwards"""
    connection = _db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = _db.create_scoped_session(options=options)

    _db.session = session
    mixer.init_app(app)

    yield session

    transaction.rollback()
    connection.close()
    session.remove()
