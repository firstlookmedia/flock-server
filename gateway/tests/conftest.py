import os
import tempfile
import pytest

from gateway import create_app
from gateway.tokens import Tokens


@pytest.fixture
def tokens():
    tokens = Tokens(tempfile.NamedTemporaryFile().name)
    yield tokens


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'TOKENS_PATH': tempfile.NamedTemporaryFile().name
    })

    yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
