from app.services.search_service import SearchService
from app.core.logger import logger
from typing import List

class ResearcherAgentService:
    def __init__(self):
        self.search_service = SearchService()

    def research(self, topic: str, concept: str) -> List[str]:
        # Formulate query: e.g. "Python Variables"
        query = f"{topic} {concept}"
        logger.info(f"ResearcherAgent: Researching query '{query}'")
        
        # Perform search
        results = self.search_service.search(query, max_results=5)
        
        # Extract URLs
        urls = [r["url"] for r in results if r.get("url")]
        logger.info(f"ResearcherAgent: Researched and retrieved {len(urls)} URLs.")
        return urls
