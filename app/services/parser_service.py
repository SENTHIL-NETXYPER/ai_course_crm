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
    try:
        return _parse_json(raw_text, "Writer")
    except ValueError:
        logger.warning("Standard JSON parsing failed for Writer. Attempting regex structure recovery...")
        chapter_match = re.search(r'"chapter"\s*:\s*"([^"]+)"', raw_text)
        chapter = chapter_match.group(1) if chapter_match else "Chapter Lesson"
        
        intro_match = re.search(r'"introduction"\s*:\s*"([^"]+)"', raw_text)
        intro = intro_match.group(1) if intro_match else "Welcome to this chapter."
        
        sections = []
        section_splits = re.split(r'"title"\s*:\s*', raw_text)[1:]
        for idx, part in enumerate(section_splits):
            title_match = re.match(r'"([^"]+)"', part)
            title = title_match.group(1) if title_match else f"Section {idx + 1}"
            
            content_match = re.search(r'"content"\s*:\s*"(.*)', part, re.DOTALL)
            if content_match:
                content_raw = content_match.group(1)
                content_clean = re.sub(r'"?\s*\}\s*,\s*(?:\{.*)?$', '', content_raw, flags=re.DOTALL)
                content_clean = re.sub(r'"?\s*\}\s*\]\s*\}\s*$', '', content_clean, flags=re.DOTALL)
                content_clean = content_clean.strip()
                if content_clean.endswith('"'):
                    content_clean = content_clean[:-1]
            else:
                content_clean = part
                
            sections.append({
                "title": title,
                "content": content_clean,
                "order": idx + 1
            })
            
        if not sections:
            sections = [{
                "title": chapter,
                "content": raw_text,
                "order": 1
            }]
            
        return {
            "chapter": chapter,
            "introduction": intro,
            "sections": sections
        }


def parse_reviewer_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Reviewer")


def parse_planner_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Planner")


def parse_organizer_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Organizer")
