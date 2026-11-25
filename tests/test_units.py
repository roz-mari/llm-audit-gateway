from app.guard import redact
from app.tools import run_tool


def test_redact_email():
    text, found = redact("write to maria@example.com")
    assert text == "write to [REDACTED_EMAIL]"
    assert found == ["email"]


def test_redact_nothing():
    assert redact("What time is it?") == ("What time is it?", [])


def test_unknown_tool():
    assert run_tool("delete_database", "{}") == "Error: unknown tool delete_database"


def test_tool_with_bad_timezone():
    assert run_tool("get_current_time", '{"timezone": "Mars/Base"}').startswith("Error")
