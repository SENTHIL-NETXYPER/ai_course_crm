from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="The chat message sent by the user")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="The assistant's response/reply")

class StructuredChatRequest(BaseModel):
    topic: str = Field(..., description="The course topic to explain (e.g. Python)")
    difficulty: str = Field(default="Beginner", description="Difficulty level (e.g. Beginner, Intermediate, Advanced)")

class StructuredChatResponse(BaseModel):
    course_name: str = Field(..., description="Name of the course")
    description: str = Field(..., description="Description of the course")
    difficulty: str = Field(..., description="Difficulty level of the course")

