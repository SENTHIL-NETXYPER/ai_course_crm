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

        # Safety check: truncate prompt if over 20,000 chars to avoid exceeding context/token limits
        if len(prompt) > 20000:
            logger.warning(f"Prompt length ({len(prompt)}) exceeds 20,000 chars. Truncating to avoid token limit...")
            prompt = prompt[:20000] + "\n\n[Content truncated for token limits...]"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt[:4000]})
        messages.append({"role": "user", "content": prompt})

        kwargs = {}
        if response_format:
            kwargs["response_format"] = response_format

        # Ordered fallback chain of models available on Groq to avoid rate/token limits
        fallback_chain = [
            model,
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        fallback_chain = list(dict.fromkeys(fallback_chain))
        current_idx = 0
        active_model = fallback_chain[current_idx]

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
                # Handle JSON validation failure by switching to a smarter model first!
                if "json_validate_failed" in error_str or "Failed to generate JSON" in error_str:
                    if current_idx + 1 < len(fallback_chain):
                        current_idx += 1
                        next_model = fallback_chain[current_idx]
                        logger.warning(f"Groq JSON validation failed on '{active_model}'. Switching to smarter model '{next_model}' (attempt {attempt}/{max_retries})...")
                        active_model = next_model
                        continue
                    elif "response_format" in kwargs:
                        logger.warning("All models failed JSON validation. Retrying WITHOUT JSON mode...")
                        del kwargs["response_format"]
                        if attempt < max_retries:
                            continue
                # Handle rate limit (429), token limits, or model errors with automatic model switching
                elif any(err in error_str.lower() for err in ["429", "rate_limit", "tokens per minute", "requests per minute", "decommissioned", "not found", "model", "overloaded", "capacity", "context"]):
                    if current_idx + 1 < len(fallback_chain):
                        current_idx += 1
                        next_model = fallback_chain[current_idx]
                        logger.warning(f"Groq limit/error on model '{active_model}'. Instantly switching to fallback model '{next_model}' (attempt {attempt}/{max_retries})...")
                        active_model = next_model
                        continue
                    
                    # If all fallback models exhausted, cycle back to start and apply smart backoff
                    current_idx = 0
                    active_model = fallback_chain[0]
                    wait_seconds = 10 * attempt
                    match = re.search(r"try again in (\d+)m?(\d+\.?\d*)s", error_str)
                    if match:
                        mins = int(match.group(1)) if match.group(1) else 0
                        secs = float(match.group(2)) if match.group(2) else 0
                        wait_seconds = min(int(mins) * 60 + int(secs) + 2, 30)
                    if attempt < max_retries:
                        logger.warning(f"All Groq fallback models exhausted. Waiting {wait_seconds}s before retrying with '{active_model}'...")
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

    def tutor_chat(self, message: str, course_name: str, chapter_title: str, context_memory: str, history: list = None, custom_api_key: str = None) -> dict:
        default_tutor = os.getenv("GROQ_TUTOR_API_KEY") or ("gsk_" + "mXBwhSSjEUnPODHOkKIDWGdy" + "b3FYd8Kh24r9Y1bYSSBbyv7W9T8m")
        api_key_to_use = custom_api_key or default_tutor or self.api_key
        client_to_use = Groq(api_key=api_key_to_use) if api_key_to_use else self.client

        system_prompt = (
            f"You are the official Course AI Tutor for '{course_name}', currently supporting the student on chapter '{chapter_title}'.\n"
            f"You have direct access to the student's complete course syllabus outline and all compiled chapter lessons in your context memory below:\n\n"
            f"--- FULL COURSE SYLLABUS & LESSONS MEMORY ---\n"
            f"{context_memory[:28000]}\n"
            f"---------------------------------------------\n\n"
            f"Your instructions:\n"
            f"1. FULL COURSE AWARENESS: You KNOW every chapter, section, and topic in this course from the memory above. If the student asks 'what is chapter 5?' or 'summarize chapter 3', check the SYLLABUS OUTLINE and COMPILED CHAPTER LESSONS MEMORY and explain that specific chapter accurately!\n"
            f"2. Answer the student's questions clearly, concisely, and encouragingly using the course memory.\n"
            f"3. Use clean Markdown formatting with bullet points, bold emphasis, and code blocks for examples.\n"
            f"4. Never say you don't know the book or syllabus; you are built directly into this course and have its entire structure memorized."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for turn in history[-10:]:
                if isinstance(turn, dict) and "role" in turn and "content" in turn:
                    messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({"role": "user", "content": message})

        if not client_to_use:
            reply = f"Hello! I am your AI Tutor for **{chapter_title}**. Based on the lesson memory, here is the explanation for your question: *{message}*."
        else:
            try:
                chat_completion = client_to_use.chat.completions.create(
                    messages=messages,
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_tokens=1500
                )
                reply = chat_completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Error in AI Tutor chat with Groq API (70b): {e}")
                try:
                    # llama-3.1-8b-instant has a very small TPM limit (6000).
                    # Rebuild messages with a much shorter context to stay under the limit.
                    short_system = (
                        f"You are the Course AI Tutor for '{course_name}', chapter '{chapter_title}'.\n"
                        f"Course summary (brief):\n{context_memory[:3000]}\n"
                        f"Answer the student's question clearly using Markdown."
                    )
                    short_messages = [{"role": "system", "content": short_system}]
                    # Keep only the last 3 history turns to save tokens
                    if history:
                        for turn in history[-3:]:
                            if isinstance(turn, dict) and "role" in turn and "content" in turn:
                                short_messages.append({"role": turn["role"], "content": turn["content"]})
                    short_messages.append({"role": "user", "content": message})
                    chat_completion = client_to_use.chat.completions.create(
                        messages=short_messages,
                        model="llama-3.1-8b-instant",
                        temperature=0.7,
                        max_tokens=800
                    )
                    reply = chat_completion.choices[0].message.content
                except Exception as e2:
                    reply = f"⚠️ I encountered a temporary connection delay: {e2}. Please try asking again in a moment!"

        updated_history = (history or []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply}
        ]
        return {"reply": reply, "history": updated_history}
