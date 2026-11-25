import os

# use SQLite in tests (must be set before importing the app)
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from openai.types.chat import ChatCompletion

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import ApiKey
from app.security import generate_key, hash_key


def fake_response(content=None, tool_calls=None) -> ChatCompletion:
    """Same object the OpenAI SDK returns, so the code under test can't tell the difference."""
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return ChatCompletion.model_validate({
        "id": "test",
        "object": "chat.completion",
        "created": 0,
        "model": "fake",
        "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    })


class FakeLLM:
    """Replaces client.chat.completions.create and returns the prepared responses in order."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def client():
    return TestClient(app)


def create_key(name):
    key = generate_key()
    with SessionLocal() as db:
        db.add(ApiKey(name=name, key_hash=hash_key(key)))
        db.commit()
    return key


@pytest.fixture
def fake_llm(monkeypatch):
    def install(responses):
        fake = FakeLLM(responses)
        monkeypatch.setattr("app.llm.get_client", lambda: fake)
        return fake

    return install
