import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router as api_router
from app.schemas.chat import ChatRequest, ChatResponse, StructuredChatRequest, StructuredChatResponse
from app.services.groq_service import GroqService
from fastapi import HTTPException
import json

from fastapi.responses import HTMLResponse
import os

app = FastAPI(
    title="Course AI API",
    description="API backend for the AI Course Generator application",
    version="0.1.0"
)

# Add CORS middleware to allow external websites and third-party backends to call our API
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any frontend or backend origin to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes with the api prefix and as root paths
app.include_router(api_router, prefix="/api")
app.include_router(api_router)

# Mount static files (serves app/static/* at /static/*)
_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

groq_service = GroqService()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        reply = groq_service.generate(prompt=request.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/structured-chat", response_model=StructuredChatResponse)
async def structured_chat(request: StructuredChatRequest):
    try:
        prompt = f"Explain the course topic: {request.topic} at a {request.difficulty} difficulty level."
        system_prompt = (
            "You are a backend API. Return ONLY valid JSON with keys: course_name, description, difficulty. "
            "Do not write markdown blocks or any text outside of the JSON."
        )
        raw_response = groq_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(raw_response)
        return StructuredChatResponse(**parsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def read_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_file_path = os.path.join(current_dir, "static", "index.html")
    if os.path.exists(static_file_path):
        with open(static_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend index.html not found!</h1>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
