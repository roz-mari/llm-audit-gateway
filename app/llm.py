from functools import lru_cache

from openai import OpenAI

from app.config import get_settings
from app.tools import TOOLS, run_tool

MAX_TOOL_ROUNDS = 3


@lru_cache
def get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def ask(question: str) -> dict:
    client = get_client()
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Answer briefly."},
        {"role": "user", "content": question},
    ]
    tools_used = []
    total_tokens = 0

    for _ in range(MAX_TOOL_ROUNDS + 1):
        response = client.chat.completions.create(
            model=get_settings().llm_model,
            messages=messages,
            tools=TOOLS,
        )
        total_tokens += response.usage.total_tokens if response.usage else 0
        message = response.choices[0].message

        # no tool needed, this is the final answer
        if not message.tool_calls:
            return {"answer": message.content or "", "tools_used": tools_used, "total_tokens": total_tokens}

        # the model asked for tools: run them and send the results back
        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            tools_used.append(call.function.name)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": run_tool(call.function.name, call.function.arguments),
            })

    raise RuntimeError("Too many tool calls")
