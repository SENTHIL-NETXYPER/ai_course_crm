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


from typing import Any


def sanitize_string(val: Any, default: str = "") -> str:
    if val is None:
        return default
    if isinstance(val, str):
        return val.strip() or default
    if isinstance(val, dict):
        for key in ["content", "description", "summary", "text", "title", "chapter", "name"]:
            if key in val and val[key] is not None:
                if isinstance(val[key], str):
                    return val[key].strip()
                elif isinstance(val[key], (dict, list)):
                    return str(val[key]).strip()
        return str(val).strip()
    if isinstance(val, list):
        parts = [sanitize_string(item, "") for item in val if item is not None]
        return "\n\n".join([p for p in parts if p]).strip() or default
    return str(val).strip() or default


def sanitize_sections(raw_sections: Any, default_title: str = "Lesson Section") -> list:
    if not isinstance(raw_sections, list):
        if isinstance(raw_sections, dict):
            if any(isinstance(v, dict) for v in raw_sections.values()):
                raw_sections = list(raw_sections.values())
            else:
                raw_sections = [raw_sections]
        elif raw_sections is not None and str(raw_sections).strip():
            raw_sections = [raw_sections]
        else:
            return [{"title": default_title, "content": "No content generated.", "order": 1}]
    
    clean_sections = []
    for idx, item in enumerate(raw_sections):
        order_val = len(clean_sections) + 1
        if isinstance(item, dict):
            title = sanitize_string(item.get("title", f"{default_title} {order_val}"), f"{default_title} {order_val}")
            content = sanitize_string(item.get("content", item.get("description", item.get("text", ""))), "")
            if not content and len(title) > 50:
                content = title
                title = title.split("\n")[0][:50] + "..."
            if not content:
                content = f"Details and examples for {title}."
            try:
                order_val = int(item.get("order", order_val))
            except (ValueError, TypeError):
                order_val = len(clean_sections) + 1
            if order_val <= 0:
                order_val = len(clean_sections) + 1
            clean_sections.append({
                "title": title,
                "content": content,
                "order": order_val
            })
        elif isinstance(item, str):
            val_str = item.strip()
            if val_str in ["order", ": 1", ":", "{", "}", "[", "]"] or re.match(r'^[\s:,0-9]+$', val_str):
                continue
            clean_sections.append({
                "title": f"{default_title} {order_val}",
                "content": val_str,
                "order": order_val
            })
        elif item is not None:
            clean_sections.append({
                "title": f"{default_title} {order_val}",
                "content": str(item),
                "order": order_val
            })
            
    if not clean_sections:
        clean_sections = [{"title": default_title, "content": "No content generated.", "order": 1}]
        
    for idx, sec in enumerate(clean_sections):
        sec["order"] = idx + 1
        
    return clean_sections


def sanitize_lesson_dict(res: Any, default_title: str = "Chapter Lesson") -> dict:
    if not isinstance(res, dict):
        res = {}
    
    chapter = sanitize_string(res.get("chapter", res.get("title", default_title)), default_title)
    intro = sanitize_string(res.get("introduction", res.get("intro", "")), f"Welcome to {chapter}.")
    sections = sanitize_sections(res.get("sections", []), "Lesson Section")
    
    return {
        "chapter": chapter,
        "introduction": intro,
        "sections": sections
    }


def parse_writer_response(raw_text: str) -> dict:
    try:
        res = _parse_json(raw_text, "Writer")
        return sanitize_lesson_dict(res)
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
            
        return sanitize_lesson_dict({
            "chapter": chapter,
            "introduction": intro,
            "sections": sections
        })


def parse_reviewer_response(raw_text: str) -> dict:
    try:
        res = _parse_json(raw_text, "Reviewer")
        if isinstance(res, dict):
            if "refined_lesson" in res and isinstance(res["refined_lesson"], dict):
                res["refined_lesson"] = sanitize_lesson_dict(res["refined_lesson"])
            if "sections" in res:
                res["sections"] = sanitize_sections(res.get("sections", []))
        return res
    except Exception as e:
        logger.warning(f"Reviewer JSON parse failed: {e}. Returning default dict.")
        return {}


def parse_planner_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Planner")


def parse_organizer_response(raw_text: str) -> dict:
    return _parse_json(raw_text, "Organizer")
