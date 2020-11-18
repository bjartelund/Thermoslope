import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_start_page(client):
    rv = client.get('/')
    assert b"Hello" in rv.data

def test_upload_page(client):
    rv = client.get('/upload')
    assert b"Upload data" in rv.data

