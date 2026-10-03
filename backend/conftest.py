import pytest

from chronicle.story_fixtures import load_story as load_story_fixture
from chronicle.tests.factories import ChronicleFactory, EntityFactory, PlayerFactory, append_beat

pytest_plugins = ["llm.pytest_plugin"]


@pytest.fixture
def chronicle(db):
    return ChronicleFactory(kind="session")


@pytest.fixture
def players(chronicle):
    return [PlayerFactory(chronicle=chronicle, name="Anna"), PlayerFactory(chronicle=chronicle, name="Ben")]


@pytest.fixture
def entity_factory(chronicle):
    def make_entity(**fields):
        return EntityFactory(chronicle=chronicle, **fields)

    return make_entity


@pytest.fixture
def beat_factory(chronicle):
    def make_beat(pred, **kwargs):
        return append_beat(chronicle, pred, **kwargs)

    return make_beat


@pytest.fixture
def load_story(db):
    return load_story_fixture
