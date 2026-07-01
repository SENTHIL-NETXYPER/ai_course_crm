import os
from app.services.groq_service import GroqService
from app.services.scrape_service import ScrapeService
from app.services.parser_service import parse_organizer_response
from app.core.logger import logger
from typing import List

# Resolve the prompt path from the central prompts directory
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "prompts")


class OrganizerAgentService:
    def __init__(self):
        self.groq_service = GroqService()
        self.scrape_service = ScrapeService()

        # Load prompt template from central prompts directory
        prompt_path = os.path.normpath(os.path.join(_PROMPTS_DIR, "organizer_prompt.txt"))
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Organizer prompt template not found at: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def organize_content(self, urls: List[str]) -> dict:
        logger.info(f"OrganizerAgent: Organizing content for {len(urls)} URLs")

        # Load and merge content from scraped files
        content_blocks = []
        for url in urls:
            filename = self.scrape_service._url_to_filename(url)
            filepath = os.path.join(self.scrape_service.output_dir, filename)

            if os.path.exists(filepath):
                logger.info(f"OrganizerAgent: Reading content from {filepath}")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content_blocks.append(f"--- CONTENT FROM URL: {url} ---\n{f.read()}\n")
                except Exception as e:
                    logger.error(f"OrganizerAgent: Error reading {filepath}: {e}")
            else:
                logger.warning(f"OrganizerAgent: Scraped file for {url} not found at {filepath}")

        if not content_blocks:
            logger.warning("OrganizerAgent: No scraped content files found. Using empty placeholder.")
            merged_content = "No content available."
        else:
            merged_content = "\n".join(content_blocks)

        # Format prompt
        prompt = self.prompt_template.format(merged_content=merged_content)
        system_prompt = "You are a professional content editor. Always reply in valid JSON containing categorized topics."

        # Request generation
        raw_response = self.groq_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )

        # Parse the response
        parsed_data = parse_organizer_response(raw_response)
        logger.info(f"Successfully organized content into {len(parsed_data.get('categories', []))} categories.")
        return parsed_data
