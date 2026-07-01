import os
from app.services.groq_service import GroqService
from app.agents.reviewer.parser import parse_reviewer_response
from app.core.logger import logger

class ReviewerAgentService:
    def __init__(self):
        self.groq_service = GroqService()
        
        # Load prompt template
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "prompt.txt")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Reviewer prompt template not found at: {prompt_path}")
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def review_lesson(self, topic: str, lesson_markdown: str, review_criteria: str = None) -> dict:
        logger.info(f"ReviewerAgent: Reviewing lesson for topic '{topic}'")
        
        # Set default criteria if none provided
        if not review_criteria:
            review_criteria = "Verify python syntax is correct, spelling/grammar is correct, formatting is clean, and explanation is clear."
            
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
