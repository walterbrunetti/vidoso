import pytest
from unittest.mock import Mock

from main import create_app, db


class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    TESTING: True
    DEBUG: True


@pytest.fixture()
def app():
    app = create_app(config_class=TestConfig)
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db"
    })
    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()