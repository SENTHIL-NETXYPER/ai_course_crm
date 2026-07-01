from pydantic import BaseModel, Field
from typing import List

class ResearchRequest(BaseModel):
    topic: str = Field(..., description="The main course topic (e.g. Python)")
    concept: str = Field(..., description="The specific concept or chapter topic to research (e.g. Variables)")

class ResearchResponse(BaseModel):
    topic: str = Field(..., description="The main course topic")
    concept: str = Field(..., description="The researched concept")
    urls: List[str] = Field(..., description="List of URLs found for the concept")
