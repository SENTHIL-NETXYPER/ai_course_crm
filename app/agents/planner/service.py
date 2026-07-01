import os
from app.services.groq_service import GroqService
from app.services.parser_service import parse_planner_response
from app.core.logger import logger

# Resolve the prompt path from the central prompts directory
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "prompts")


class PlannerAgentService:
    def __init__(self):
        self.groq_service = GroqService()

        # Load prompt template from central prompts directory
        prompt_path = os.path.normpath(os.path.join(_PROMPTS_DIR, "planner_prompt.txt"))
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Planner prompt template not found at: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def generate_plan(self, topic: str) -> dict:
        logger.info(f"Generating course plan for topic: {topic}")

        # Format user prompt with the topic
        prompt = self.prompt_template.format(topic=topic)
        system_prompt = "You are an expert syllabus creator. Always reply in valid JSON containing course name and chapters."

        # Request generation
        raw_response = self.groq_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )

        # Parse the JSON response
        parsed_data = parse_planner_response(raw_response)
        logger.info(f"Successfully generated course plan with {len(parsed_data.get('chapters', []))} chapters.")
        return parsed_data
