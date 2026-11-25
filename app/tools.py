import json
from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time(timezone: str = "Europe/Madrid") -> str:
    return datetime.now(ZoneInfo(timezone)).isoformat(timespec="seconds")


# Schema sent to the model so it knows the tool exists
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in a time zone, e.g. Europe/Madrid",
            "parameters": {
                "type": "object",
                "properties": {"timezone": {"type": "string"}},
            },
        },
    },
]

FUNCTIONS = {"get_current_time": get_current_time}


def run_tool(name: str, arguments: str) -> str:
    if name not in FUNCTIONS:
        return f"Error: unknown tool {name}"
    try:
        return FUNCTIONS[name](**json.loads(arguments or "{}"))
    except Exception as e:
        # send the error back to the model instead of crashing
        return f"Error: {e}"
