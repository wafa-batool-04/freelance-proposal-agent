from __future__ import annotations

import json


def parse_llm_json(response: str) -> dict:
    """Parse a JSON object from an LLM response, tolerating markdown wrappers."""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(
                f"No JSON object found in LLM response: {response[:200]!r}"
            )
        return json.loads(response[start:end])
