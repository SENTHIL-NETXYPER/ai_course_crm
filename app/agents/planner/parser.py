import json
import re
from app.core.logger import logger

def parse_planner_response(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    
    # Try standard json loads first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
        
    # Try anchored markdown code block extraction
    match = re.search(r'^\s*```(?:json)?\s*(.*?)\s*```\s*$', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
            
    # Try finding first '{' and last '}' as a fallback
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end+1])
        except json.JSONDecodeError:
            pass
            
    logger.error(f"Failed to parse text as JSON. Raw text content: {raw_text}")
    raise ValueError(f"Failed to parse Planner response as JSON: raw content is not valid JSON")
