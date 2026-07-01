from pydantic import BaseModel, Field

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="The HTTP/HTTPS URL of the web page to scrape")

class ScrapeResponse(BaseModel):
    success: bool = Field(..., description="Indicates if scraping succeeded")
    saved_filename: str = Field(..., description="The name of the saved markdown file")
    markdown_snippet: str = Field(..., description="A snippet of the extracted markdown content")
