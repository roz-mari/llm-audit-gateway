from tests.conftest import create_key, fake_response


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_without_key(client):
    response = client.post("/v1/ask", json={"question": "hi"})
    assert response.status_code == 401


def test_ask_with_wrong_key(client):
    response = client.post("/v1/ask", json={"question": "hi"}, headers={"X-API-Key": "gw_wrong"})
    assert response.status_code == 401


def test_ask_saves_log(client, fake_llm):
    key = create_key("test")
    fake_llm([fake_response("Hello!")])

    response = client.post("/v1/ask", json={"question": "Say hello"}, headers={"X-API-Key": key})

    assert response.status_code == 200
    assert response.json()["answer"] == "Hello!"
    logs = client.get("/v1/logs", headers={"X-API-Key": key}).json()
    assert len(logs) == 1
    assert logs[0]["total_tokens"] == 15


def test_tool_call(client, fake_llm):
    key = create_key("test")
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "get_current_time", "arguments": '{"timezone": "Europe/Madrid"}'},
    }
    fake = fake_llm([fake_response(tool_calls=[tool_call]), fake_response("It's 13:00.")])

    response = client.post("/v1/ask", json={"question": "What time is it?"}, headers={"X-API-Key": key})

    assert response.json()["tools_used"] == ["get_current_time"]
    # the second request to the model must include the tool result
    last_message = fake.calls[1]["messages"][-1]
    assert last_message["role"] == "tool"
    assert last_message["tool_call_id"] == "call_1"


def test_sensitive_data_is_not_sent_to_model(client, fake_llm):
    key = create_key("test")
    fake = fake_llm([fake_response("Ok")])

    response = client.post(
        "/v1/ask",
        json={"question": "My email is maria@example.com and key sk-proj-ABCDEFGHIJKLMNOP1234"},
        headers={"X-API-Key": key},
    )

    sent = fake.calls[0]["messages"][-1]["content"]
    assert "maria@example.com" not in sent
    assert "sk-proj" not in sent
    assert response.json()["redactions"] == ["email", "api_key"]


def test_client_cannot_see_other_logs(client, fake_llm):
    key_a = create_key("a")
    key_b = create_key("b")
    fake_llm([fake_response("Ok")])
    client.post("/v1/ask", json={"question": "hi"}, headers={"X-API-Key": key_a})

    assert client.get("/v1/logs", headers={"X-API-Key": key_b}).json() == []


def test_provider_error_is_logged(client, monkeypatch):
    key = create_key("test")

    def broken(prompt):
        raise RuntimeError("provider is down")

    monkeypatch.setattr("app.llm.ask", broken)

    response = client.post("/v1/ask", json={"question": "hi"}, headers={"X-API-Key": key})

    assert response.status_code == 502
    logs = client.get("/v1/logs", headers={"X-API-Key": key}).json()
    assert logs[0]["status"] == "error"


def test_empty_question(client):
    key = create_key("test")
    response = client.post("/v1/ask", json={"question": ""}, headers={"X-API-Key": key})
    assert response.status_code == 422
