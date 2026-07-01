import os
from app.services.groq_service import GroqService
from app.core.logger import logger

from app.agents.writer.parser import parse_writer_response

class WriterAgentService:
    def __init__(self):
        self.groq_service = GroqService()
        
        # Load prompt template
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "prompt.txt")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Writer prompt template not found at: {prompt_path}")
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def write_lesson(self, topic: str, knowledge: str, style_template: str = None) -> dict:
        logger.info(f"WriterAgent: Writing structured lesson for topic '{topic}'")
        
        # Set default style template if empty
        if not style_template:
            style_template = "Format sections as clean Markdown, include clear section headings, explanations, and Python code blocks."
            
        # Format the user prompt
        prompt = self.prompt_template.format(
            topic=topic,
            knowledge=knowledge,
            style_template=style_template
        )
        
        system_prompt = "You are an expert technical content writer. You synthesize knowledge into a structured JSON lesson outline."
        
        # Call Groq service
        raw_response = self.groq_service.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Parse the JSON response
        parsed_data = parse_writer_response(raw_response)
        logger.info(f"Successfully generated structured lesson for '{topic}' with {len(parsed_data.get('sections', []))} sections.")
        return parsed_data
