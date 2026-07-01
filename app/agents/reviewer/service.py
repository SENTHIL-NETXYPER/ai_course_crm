import os
from app.services.groq_service import GroqService
from app.services.parser_service import parse_reviewer_response
from app.core.logger import logger

# Resolve the prompt path from the central prompts directory
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "prompts")


class ReviewerAgentService:
    def __init__(self):
        self.groq_service = GroqService()

        # Load prompt template from central prompts directory
        prompt_path = os.path.normpath(os.path.join(_PROMPTS_DIR, "reviewer_prompt.txt"))
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Reviewer prompt template not found at: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def review_lesson(self, topic: str, lesson_markdown: str, review_criteria: str = None) -> dict:
        logger.info(f"ReviewerAgent: Reviewing lesson for topic '{topic}'")

        # Set default criteria if none provided
        if not review_criteria:
            review_criteria = "Verify syntax is correct, spelling/grammar is correct, formatting is clean, and explanation is clear."

        # Format the user prompt
        prompt = self.prompt_template.format(
            topic=topic,
            lesson_markdown=lesson_markdown,
            review_criteria=review_criteria
        )

        system_prompt = "You are a professional editor. Always reply in valid JSON containing review metrics, feedback, and a structured refined_lesson."

        # Call Groq service
        raw_response = self.groq_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )

        # Parse the response
        parsed_data = parse_reviewer_response(raw_response)
        logger.info(f"Successfully reviewed lesson for '{topic}' (Approved: {parsed_data.get('approved')}).")
        return parsed_data
