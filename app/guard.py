import re

# Data that should never be sent to the LLM provider
PATTERNS = {
    "email": re.compile(r"[\w.+]+@[\w]+\.[\w.]+"),
    "api_key": re.compile(r"\b(sk|gw)[-_][A-Za-z0-9_-]{16,}"),
}


def redact(text: str) -> tuple[str, list[str]]:
    found = []
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            found.append(name)
            text = pattern.sub(f"[REDACTED_{name.upper()}]", text)
    return text, found
