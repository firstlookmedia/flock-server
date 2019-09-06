import os
import pytest

from elasticsearch_dsl import Index, Search
from flock_server import create_api_app


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_api_app({
        'TESTING': True
    })

    yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    app = app.test_client()

    # Delete all users
    Search(index='user').query('match_all').delete()
    Index('user').refresh()

    return app
