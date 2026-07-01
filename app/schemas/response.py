from pydantic import BaseModel, Field
from typing import List

class ChapterOutline(BaseModel):
    id: int = Field(..., description="The sequence ID of the chapter")
    title: str = Field(..., description="Title of the chapter")

class Course(BaseModel):
    id: str = Field(..., description="Slugified unique course identifier (e.g. python)")
    course: str = Field(..., description="Name of the course")
    chapters: List[ChapterOutline] = Field(..., description="List of chapters in this course")

class CourseGenerationSuccess(BaseModel):
    success: bool = Field(..., description="True if roadmap generation succeeded")
    course_id: str = Field(..., description="Slugified course identifier")
    course_name: str = Field(..., description="Course name")

class ChapterCompileResponse(BaseModel):
    status: str = Field(..., description="Status of compiling (e.g. completed)")

class SectionDetail(BaseModel):
    title: str = Field(..., description="Title of the section")
    content: str = Field(..., description="Detailed content in markdown format")
    order: int = Field(..., description="Display order of the section")

class ChapterDetail(BaseModel):
    chapter_id: int = Field(..., description="The ID of the chapter")
    course_id: str = Field(..., description="The ID of the course")
    title: str = Field(..., description="Title of the chapter")
    introduction: str = Field(..., description="Brief introductory overview")
    sections: List[SectionDetail] = Field(..., description="List of lesson sections")

class CourseResearchResponse(BaseModel):
    course_id: str = Field(..., description="The course ID")
    concept: str = Field(..., description="The researched concept")
    urls: List[str] = Field(..., description="Top researched URLs")
