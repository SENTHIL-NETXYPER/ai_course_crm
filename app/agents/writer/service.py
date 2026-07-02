import os
from app.services.groq_service import GroqService
from app.services.parser_service import parse_writer_response
from app.core.logger import logger

# Resolve the prompt path from the central prompts directory
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "prompts")


class WriterAgentService:
    def __init__(self):
        self.groq_service = GroqService()

        # Load prompt template from central prompts directory
        prompt_path = os.path.normpath(os.path.join(_PROMPTS_DIR, "writer_prompt.txt"))
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Writer prompt template not found at: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def write_lesson(self, topic: str, knowledge: str, style_template: str = None, course_name: str = "") -> dict:
        logger.info(f"WriterAgent: Writing structured lesson for topic '{topic}' (course: '{course_name}')")

        # Set default style template if empty
        if not style_template:
            style_template = f"Format sections as clean Markdown, include clear section headings, in-depth technical explanations, and rich, well-commented code examples strictly in {course_name if course_name else 'the target language'}."

        # Format the user prompt
        prompt = self.prompt_template.format(
            topic=topic,
            knowledge=knowledge,
            style_template=style_template,
            course_name=course_name if course_name else topic
        )

        system_prompt = f"You are an expert technical content writer and curriculum developer for {course_name if course_name else 'technical software courses'}. You synthesize knowledge into a rich, structured JSON lesson outline."

        # Call Groq service
        raw_response = self.groq_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )

        # Parse the JSON response
        parsed_data = parse_writer_response(raw_response)
        logger.info(f"Successfully generated structured lesson for '{topic}' with {len(parsed_data.get('sections', []))} sections.")
        return parsed_data
