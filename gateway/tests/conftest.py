import os
import tempfile
import pytest

from gateway.tokens import Tokens


@pytest.fixture
def tokens():
    tokens = Tokens(tempfile.NamedTemporaryFile().name)
    yield tokens
