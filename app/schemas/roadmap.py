from pydantic import BaseModel, Field
from typing import List, Optional

class Section(BaseModel):
    title: str = Field(..., description="Title of the section")
    content: Optional[str] = Field(None, description="Content or details of the section (e.g. markdown text, code blocks)")
    order: int = Field(..., description="Sequential order of the section")

class Lesson(BaseModel):
    title: str = Field(..., description="Title of the lesson")
    description: Optional[str] = Field(None, description="Brief description of what the lesson covers")
    order: int = Field(..., description="Sequential order of the lesson")
    sections: List[Section] = Field(default_factory=list, description="List of sections within the lesson")

class Topic(BaseModel):
    title: str = Field(..., description="Title of the topic")
    description: Optional[str] = Field(None, description="Brief description of the topic")
    order: int = Field(..., description="Sequential order of the topic")
    lessons: List[Lesson] = Field(default_factory=list, description="List of lessons under this topic")

class Chapter(BaseModel):
    title: str = Field(..., description="Title of the chapter")
    description: Optional[str] = Field(None, description="Brief description of the chapter")
    order: int = Field(..., description="Sequential order of the chapter")
    topics: List[Topic] = Field(default_factory=list, description="List of topics under this chapter")

class Roadmap(BaseModel):
    title: str = Field(..., description="Title of the roadmap")
    description: Optional[str] = Field(None, description="Overview of what the roadmap covers")
    target_audience: str = Field(..., description="Intended audience level")
    chapters: List[Chapter] = Field(default_factory=list, description="List of chapters in the roadmap")
