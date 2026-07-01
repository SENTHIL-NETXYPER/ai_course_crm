from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.writer import WriteResponse

class ReviewRequest(BaseModel):
    topic: str = Field(..., description="The topic/lesson title")
    lesson_markdown: str = Field(..., description="The generated lesson content JSON string to review")
    review_criteria: Optional[str] = Field(None, description="Optional custom criteria or focus areas for the review")

class ReviewResponse(BaseModel):
    approved: bool = Field(..., description="True if the lesson passes review criteria, False otherwise")
    feedback: str = Field(..., description="Reviewer feedback and comments on the content")
    refined_lesson: Optional[WriteResponse] = Field(None, description="Polished version of the lesson if refinements were made")
