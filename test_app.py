import pytest
import os
from app import app as flask_app
thermoslope = __import__("thermofit-gradient")


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


def test_upload_single(client):
    datafile = 'exampledata/CM/BpCM/2020 2 12 10 21.csv'
    datahandle = open(datafile, "rb")

    data = {"file": (datahandle, "test.csv")}
    rv = client.post("/upload", data=data, follow_redirects=False)
    datahandle.close()
    global arg
    arg = rv.location.split("/")  # for next test
    assert "/analyze" in rv.location


def test_analysis(client):
    rv = client.get(arg[3])
    assert b"Arrhenius and thermodynamic parameters of activation barrier" in rv.data
    assert b"NaN" not in rv.data


def test_offline():
    exampledir = "exampledata/CM/BpCM/"

    datafiles = [x for x in os.listdir(
        exampledir) if not "png" in x and not "json" in x]
    analysis = thermoslope.ThermoSlope(
        [os.path.join(exampledir, datafile) for datafile in datafiles])
    analysis.process()
    assert not analysis.arrheniusparameters.empty
