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

class TutorChatRequest(BaseModel):
    message: str = Field(..., description="The chat message or question from the student")
    course_name: str = Field(default="", description="Name of the active course")
    chapter_title: str = Field(default="", description="Title of the active chapter")
    context_memory: str = Field(default="", description="Generated lesson content as context memory")
    history: list = Field(default_factory=list, description="List of previous conversation turns")
    api_key: str = Field(default="", description="Optional custom Groq API key for the AI Tutor")

class TutorChatResponse(BaseModel):
    reply: str = Field(..., description="AI Tutor response")
    history: list = Field(..., description="Updated conversation history")

