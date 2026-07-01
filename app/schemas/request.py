from pydantic import BaseModel, Field

class CourseGenerateRequest(BaseModel):
    topic: str = Field(..., description="The main topic of the course to plan (e.g. Python)")
    level: str = Field(default="beginner", description="Audience level (e.g. beginner, intermediate, advanced)")

class CourseResearchRequest(BaseModel):
    concept: str = Field(..., description="The specific concept to search for (e.g. Variables)")

class ChapterGenerateRequest(BaseModel):
    course_id: str = Field(..., description="The ID (slugified topic) of the course")
    knowledge: str = Field(..., description="The organized knowledge summary block to compile into a lesson")

class ChapterCompileRequest(BaseModel):
    course_id: str = Field(..., description="The ID (slugified topic) of the course")
    chapter_title: str = Field(default="", description="The title of the chapter (passed from frontend to avoid DB lookup)")
    regenerate: bool = Field(default=False, description="True to force recompiling")
    quick_mode: bool = Field(default=False, description="True to skip reviewer (1 Groq call vs 2). Used for bulk background compilation to avoid rate limits.")
