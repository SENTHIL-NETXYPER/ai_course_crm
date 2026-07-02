import json
import re
from app.core.logger import logger


def _sanitize_json(text: str) -> str:
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([\]}])', r'\1', text)
    # Fix unescaped physical newlines preceded by a backslash
    text = re.sub(r'\\\n', '\\n', text)
    # Replace single backslash escape sequences that are invalid in JSON (not ", \, /, b, f, n, r, t, u)
    text = re.sub(r'\\([^"\\/bfnrtu0-9])', r'\\\\\1', text)
    return text


def _parse_json(raw_text: str, context: str) -> dict:
    """
    Shared JSON parsing logic with 4-tier fallback:
      1. Direct json.loads (strict=False)
      2. Markdown code-block extraction
      3. First '{' to last '}' extraction
      4. Sanitized extraction (cleaning invalid escapes & trailing commas)
    """
    cleaned = raw_text.strip()

    # Tier 1: direct parse
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        pass

    # Tier 2: markdown code block (non-anchored to handle leading/trailing text)
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL)
    if match:
        target = match.group(1).strip()
        try:
            return json.loads(target, strict=False)
        except json.JSONDecodeError:
            try:
                return json.loads(_sanitize_json(target), strict=False)
            except json.JSONDecodeError:
                pass

    # Tier 3: first { ... last }
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1:
        target = cleaned[start:end + 1]
        try:
            return json.loads(target, strict=False)
        except json.JSONDecodeError:
            try:
                return json.loads(_sanitize_json(target), strict=False)
            except json.JSONDecodeError:
                pass

    # Tier 4: sanitize raw cleaned string directly
    try:
        return json.loads(_sanitize_json(cleaned), strict=False)
    except json.JSONDecodeError:
        pass

    logger.error(f"Failed to parse {context} response as JSON. Raw text: {raw_text}")
    raise ValueError(f"Failed to parse {context} response as JSON: content is not valid JSON")


def parse_writer_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Writer")


def parse_reviewer_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Reviewer")


def parse_planner_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Planner")


def parse_organizer_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Organizer")
