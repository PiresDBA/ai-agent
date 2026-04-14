import json


def safe_json_load(text: str):
    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()
    text = text.replace("```json", "").replace("```", "")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(f"No JSON found: {text}")

        return json.loads(text[start:end + 1])