import os
import time
import re
from groq import Groq
from app.core.logger import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GroqService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable is not set. GroqService will run in MOCK mode.")
            self.client = None
        else:
            logger.info("GroqService initialized successfully with API key.")
            self.client = Groq(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: str = None, model: str = "llama-3.1-8b-instant", response_format: dict = None, max_retries: int = 5) -> str:
        if not self.client:
            logger.info("GroqService (MOCK MODE): Generating mock response for prompt.")
            if "course_name" in (system_prompt or "") or "structured-chat" in prompt:
                return """{
  "course_name": "Python",
  "description": "A high-level programming language known for its readability and simplicity.",
  "difficulty": "Beginner"
}"""
            if "Content Organizer AI" in prompt or "Merged Content:" in prompt:
                return """{
  "categories": [
    {
      "name": "Definition",
      "description": "Core concepts and definitions of Python variables.",
      "topics": [
        {
          "title": "What is a Variable",
          "summary": "A variable is a named storage location that holds data which can be modified during program execution."
        }
      ]
    },
    {
      "name": "Syntax",
      "description": "Rules for declaring and using variables in Python.",
      "topics": [
        {
          "title": "Assignment Statement",
          "summary": "Variables are created using the assignment operator (=) where the name is on the left and value is on the right."
        }
      ]
    },
    {
      "name": "Examples",
      "description": "Code demonstrations of variables.",
      "topics": [
        {
          "title": "Variable Declaration Examples",
          "summary": "Examples of string, integer, float, and boolean variables assigned to names."
        }
      ]
    },
    {
      "name": "History",
      "description": "Context of Python variable type systems.",
      "topics": [
        {
          "title": "Dynamic Typing Evolution",
          "summary": "Python was designed from its inception to be dynamically typed, which avoids separate declaration keywords like var or let."
        }
      ]
    },
    {
      "name": "Best Practices",
      "description": "Coding styles and conventions.",
      "topics": [
        {
          "title": "Naming Conventions",
          "summary": "Always use snake_case for variables, keep names descriptive, and avoid overriding built-in functions."
        }
      ]
    },
    {
      "name": "Summary",
      "description": "Key takeaways.",
      "topics": [
        {
          "title": "Essential Takeaways",
          "summary": "Python variables are labels pointing to objects, declared via assignment, follow snake_case, and have dynamic typing."
        }
      ]
    }
  ]
}"""
            
            if "AI Writer Agent" in prompt or "Source Knowledge:" in prompt:
                return """{
  "chapter": "Variables",
  "introduction": "An introduction to variables in Python, covering dynamic typing and declaration.",
  "sections": [
    {
      "title": "Variable Declaration",
      "content": "In Python, variables are created when they are assigned a value: \\n```python\\nx = 5\\n```",
      "order": 1
    }
  ]
}"""
            
            if "AI Reviewer Agent" in prompt or "Lesson Content (JSON):" in prompt:
                import json
                mock_data = {
                    "approved": True,
                    "feedback": "The lesson structure is excellent. Code snippets are accurate and clear. No grammatical or layout errors found. Approving content.",
                    "refined_lesson": {
                        "chapter": "Variables",
                        "introduction": "An introduction to variables in Python, covering dynamic typing and declaration.",
                        "sections": [
                            {
                                "title": "Variable Declaration",
                                "content": "In Python, variables are created when they are assigned a value: \n```python\nx = 5\n```",
                                "order": 1
                            }
                        ]
                    }
                }
                return json.dumps(mock_data)
            
            # Simple heuristic to extract topic from prompt
            topic = "Python"
            if "Topic: " in prompt:
                lines = prompt.split("\n")
                for line in lines:
                    if line.startswith("Topic: "):
                        topic = line.replace("Topic: ", "").strip()
                        break
            
            mock_json = f"""{{
  "course": "{topic}",
  "chapters": [
    {{
      "id": 1,
      "title": "Introduction to {topic}"
    }},
    {{
      "id": 2,
      "title": "Control Flow and Functions in {topic}"
    }},
    {{
      "id": 3,
      "title": "Data Structures and Collections in {topic}"
    }},
    {{
      "id": 4,
      "title": "Object-Oriented Programming in {topic}"
    }}
  ]
}}"""
            return mock_json

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {}
        if response_format:
            kwargs["response_format"] = response_format

        active_model = model

        for attempt in range(1, max_retries + 1):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=active_model,
                    **kwargs
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                error_str = str(e)
                # Handle JSON validation failure
                if "json_validate_failed" in error_str or "Failed to generate JSON" in error_str:
                    logger.warning(f"Groq JSON validation failed (attempt {attempt}/{max_retries}). Retrying WITHOUT JSON mode...")
                    if "response_format" in kwargs:
                        del kwargs["response_format"]
                    if attempt < max_retries:
                        continue
                # Handle rate limit (429) with smart backoff & model fallback
                elif "429" in error_str or "rate_limit_exceeded" in error_str:
                    if active_model != "llama-3.1-8b-instant":
                        logger.warning(f"Groq rate limit hit for model {active_model}. Falling back to llama-3.1-8b-instant...")
                        active_model = "llama-3.1-8b-instant"
                        continue

                    wait_seconds = 12 * attempt  # default backoff: 12s, 24s, 36s...
                    match = re.search(r"try again in (\d+)m?(\d+\.?\d*)s", error_str)
                    if match:
                        mins = int(match.group(1)) if match.group(1) else 0
                        secs = float(match.group(2)) if match.group(2) else 0
                        parsed = int(mins) * 60 + int(secs) + 3  # +3s buffer
                        wait_seconds = min(parsed, 45)  # cap at 45s max
                    if attempt < max_retries:
                        logger.warning(f"Groq rate limit hit (attempt {attempt}/{max_retries}). Waiting {wait_seconds}s before retry...")
                        time.sleep(wait_seconds)
                        continue
                # Handle temporary server/connection errors (500, 502, 503, timeout)
                elif any(code in error_str for code in ["500", "502", "503", "504", "Connection", "Timeout"]):
                    if attempt < max_retries:
                        wait_time = 5 * attempt
                        logger.warning(f"Groq server/network error '{error_str[:50]}' (attempt {attempt}/{max_retries}). Backing off {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Error calling Groq API (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    raise e
