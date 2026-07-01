from pydantic import BaseModel, Field
from typing import List, Optional

class SectionPlan(BaseModel):
    title: str = Field(..., description="Title of the section")
    content: str = Field(..., description="Detailed content of the section in markdown format")
    order: int = Field(..., description="Display order of the section")

class WriteRequest(BaseModel):
    topic: str = Field(..., description="The topic/lesson title to write (e.g. Python Variables)")
    knowledge: str = Field(..., description="The organized knowledge summary to use as source information")
    style_template: Optional[str] = Field(None, description="Optional style guidelines or markdown template instructions")

class WriteResponse(BaseModel):
    chapter: str = Field(..., description="The chapter title (e.g. Variables)")
    introduction: str = Field(..., description="A brief introduction to the chapter")
    sections: List[SectionPlan] = Field(..., description="List of organized content sections in this chapter")
