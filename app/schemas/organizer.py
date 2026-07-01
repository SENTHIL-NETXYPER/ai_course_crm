from pydantic import BaseModel, Field
from typing import List

class OrganizerTopic(BaseModel):
    title: str = Field(..., description="The title of the topic/lesson concept")
    summary: str = Field(..., description="Summarized details of the topic with duplicate information removed")

class OrganizerCategory(BaseModel):
    name: str = Field(..., description="The name of the category")
    description: str = Field(..., description="Description of what this category covers")
    topics: List[OrganizerTopic] = Field(..., description="List of topics inside this category")

class OrganizeRequest(BaseModel):
    urls: List[str] = Field(..., description="List of scraped URLs to organize")

class OrganizeResponse(BaseModel):
    categories: List[OrganizerCategory] = Field(..., description="Organized categories and topics")
