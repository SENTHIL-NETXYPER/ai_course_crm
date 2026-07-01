from fastapi import APIRouter, HTTPException
from typing import List
import json
import re

# Request Schemas
from app.schemas.request import (
    CourseGenerateRequest, 
    CourseResearchRequest, 
    ChapterGenerateRequest,
    ChapterCompileRequest
)

# Response Schemas
from app.schemas.response import (
    Course, 
    ChapterOutline, 
    ChapterDetail, 
    SectionDetail, 
    CourseResearchResponse,
    CourseGenerationSuccess,
    ChapterCompileResponse
)
from app.schemas.chat import ChatRequest, ChatResponse, StructuredChatRequest, StructuredChatResponse
from app.schemas.scrape import ScrapeRequest, ScrapeResponse
from app.schemas.organizer import OrganizeRequest, OrganizeResponse
from app.schemas.reviewer import ReviewRequest, ReviewResponse

# Services
from app.agents.planner.service import PlannerAgentService
from app.agents.researcher.service import ResearcherAgentService
from app.agents.organizer.service import OrganizerAgentService
from app.agents.writer.service import WriterAgentService
from app.agents.reviewer.service import ReviewerAgentService
from app.services.scrape_service import ScrapeService
from app.services.groq_service import GroqService
from app.core.logger import logger
from app.database.manager import db

router = APIRouter()
planner_service = PlannerAgentService()
researcher_service = ResearcherAgentService()
scrape_service = ScrapeService()
organizer_service = OrganizerAgentService()
writer_service = WriterAgentService()
reviewer_service = ReviewerAgentService()
groq_service = GroqService()

def slugify(text: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')
    return slug if slug else "course"

@router.get("/courses", response_model=List[Course])
async def get_all_courses():
    try:
        raw_courses = db.get_all_roadmaps()
        courses_list = []
        for c in raw_courses:
            courses_list.append(Course(**c["roadmap"]))
        return courses_list
    except Exception as e:
        logger.error(f"Error fetching all courses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: str):
    try:
        cached = db.get_roadmap(course_id)
        if not cached:
            raise HTTPException(status_code=404, detail=f"Course with ID '{course_id}' not found.")
        return Course(**cached)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/generate", response_model=CourseGenerationSuccess)
async def generate_course(request: CourseGenerateRequest):
    try:
        course_id = slugify(request.topic)
        logger.info(f"Received request to generate course roadmap for topic: {request.topic} (ID: {course_id})")
        
        # Check cache
        cached = db.get_roadmap(course_id)
        if cached:
            logger.info(f"Course cache HIT for ID: {course_id}")
            return CourseGenerationSuccess(
                success=True,
                course_id=course_id,
                course_name=cached.get("course", request.topic)
            )
            
        logger.info(f"Course cache MISS for ID: {course_id}. Generating roadmap using Planner Agent...")
        plan = planner_service.generate_plan(topic=request.topic)
        
        course_data = {
            "id": course_id,
            "course": plan.get("course", request.topic),
            "chapters": plan.get("chapters", [])
        }
        
        db.save_roadmap(course_id, course_data)
        
        return CourseGenerationSuccess(
            success=True,
            course_id=course_id,
            course_name=course_data["course"]
        )
    except Exception as e:
        logger.error(f"Failed to generate course roadmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/{course_id}/research", response_model=CourseResearchResponse)
async def research_course_concept(course_id: str, request: CourseResearchRequest):
    try:
        logger.info(f"Received research request for course ID: '{course_id}', concept: '{request.concept}'")
        course_outline = db.get_roadmap(course_id)
        search_topic = course_outline.get("course", course_id) if course_outline else course_id
        
        urls = researcher_service.research(topic=search_topic, concept=request.concept)
        return CourseResearchResponse(course_id=course_id, concept=request.concept, urls=urls)
    except Exception as e:
        logger.error(f"Course research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chapters/{chapter_id}", response_model=ChapterDetail)
async def get_chapter(chapter_id: int, course_id: str):
    try:
        cached = db.get_lesson(course_id, chapter_id)
        if not cached:
            raise HTTPException(status_code=404, detail=f"Chapter {chapter_id} of Course '{course_id}' not found.")
        return ChapterDetail(**cached)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching chapter detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chapters/{chapter_id}/generate", response_model=ChapterCompileResponse)
async def generate_chapter_lesson(chapter_id: int, request: ChapterCompileRequest):
    try:
        course_id = request.course_id
        logger.info(f"Received request to compile chapter {chapter_id} of course '{course_id}'")
        
        # Check cache if not force-regenerate
        if not request.regenerate:
            cached = db.get_lesson(course_id, chapter_id)
            if cached:
                logger.info(f"Chapter compile cache HIT for course '{course_id}', chapter {chapter_id}")
                return ChapterCompileResponse(status="completed")
                
        logger.info(f"Chapter compile cache MISS or forced regenerate. Resolving chapter details...")
        
        course_outline = db.get_roadmap(course_id)
        if not course_outline:
            raise HTTPException(status_code=404, detail=f"Course syllabus roadmap for ID '{course_id}' not found.")
            
        chapter_title = f"Chapter {chapter_id}"
        for ch in course_outline.get("chapters", []):
            if ch.get("id") == chapter_id:
                chapter_title = ch.get("title", chapter_title)
                break
                
        # 1. Research Agent (web references lookup)
        urls = []
        try:
            urls = researcher_service.research(topic=course_outline.get("course", course_id), concept=chapter_title)
        except Exception as re_err:
            logger.error(f"Research failed for chapter {chapter_id}: {re_err}")
            
        # 2. Scrape & Organize (Knowledge builder)
        knowledge_block = f"Core information about {chapter_title}."
        if urls:
            try:
                scraped_content = scrape_service.scrape(url=urls[0])
                organized_data = organizer_service.organize_content(urls=[urls[0]])
                knowledge_block = "\n\n".join([
                    f"Category: {cat['name']}\n" + "\n".join([f"{t['title']}: {t['summary']}" for t in cat.get("topics", [])])
                    for cat in organized_data.get("categories", [])
                ])
            except Exception as scr_err:
                logger.error(f"Scraper/Organizer failed for chapter {chapter_id}: {scr_err}")
                
        # 3. Writer & Reviewer (Self-Reflection Loop)
        max_attempts = 3
        current_style = "Format sections as clean Markdown, include clear section headings, explanations, and Python code blocks."
        last_lesson = None
        chapter_detail = None
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Attempt {attempt}/{max_attempts} to write lesson...")
            try:
                last_lesson = writer_service.write_lesson(
                    topic=chapter_title,
                    knowledge=knowledge_block,
                    style_template=current_style
                )
                lesson_str = json.dumps(last_lesson)
                
                review_result = reviewer_service.review_lesson(
                    topic=chapter_title,
                    lesson_markdown=lesson_str,
                    review_criteria="Check for missing sections, duplicate content, wrong order, and empty explanation."
                )
                
                if review_result.get("approved"):
                    logger.info(f"Lesson approved by Reviewer on attempt {attempt}!")
                    final_outline = review_result.get("refined_lesson") or last_lesson
                    chapter_detail = {
                        "chapter_id": chapter_id,
                        "course_id": course_id,
                        "title": final_outline.get("chapter", chapter_title),
                        "introduction": final_outline.get("introduction", ""),
                        "sections": final_outline.get("sections", [])
                    }
                    break
                else:
                    logger.warning(f"Reviewer rejected draft on attempt {attempt}. Feedback: {review_result.get('feedback')}")
                    current_style = f"{current_style}\n\nReviewer feedback on last draft: {review_result.get('feedback')}"
            except Exception as loop_err:
                logger.error(f"Error in writer/reviewer loop on attempt {attempt}: {loop_err}")
                
        if not chapter_detail:
            logger.warning(f"Falling back to draft format.")
            chapter_detail = {
                "chapter_id": chapter_id,
                "course_id": course_id,
                "title": last_lesson.get("chapter", chapter_title) if last_lesson else chapter_title,
                "introduction": last_lesson.get("introduction", "") if last_lesson else "",
                "sections": last_lesson.get("sections", []) if last_lesson else []
            }
            
        # Save compiled lesson to SQLite database
        db.save_lesson(course_id, chapter_id, chapter_detail)
        logger.info(f"Successfully compiled and saved chapter {chapter_id} to database.")
        
        return ChapterCompileResponse(status="completed")
    except Exception as e:
        logger.error(f"Failed to generate chapter lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================= Standalone Agent Endpoints (For swagger load-testing) =================

@router.post("/planner/generate")
async def standalone_planner(request: CourseGenerateRequest):
    try:
        plan = planner_service.generate_plan(topic=request.topic)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research")
async def standalone_researcher(request: CourseResearchRequest):
    try:
        urls = researcher_service.research(topic="General", concept=request.concept)
        return {"sources": [{"title": f"Source for {request.concept}", "url": url} for url in urls]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape", response_model=ScrapeResponse)
async def standalone_scraper(request: ScrapeRequest):
    try:
        markdown_content = scrape_service.scrape(url=request.url)
        filename = scrape_service._url_to_filename(request.url)
        snippet = markdown_content[:300] + "..." if len(markdown_content) > 300 else markdown_content
        return ScrapeResponse(success=True, saved_filename=filename, markdown_snippet=snippet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/organize", response_model=OrganizeResponse)
async def standalone_organizer(request: OrganizeRequest):
    try:
        organized_data = organizer_service.organize_content(urls=request.urls)
        return OrganizeResponse(**organized_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/write-lesson")
async def standalone_writer(request: ChapterGenerateRequest):
    try:
        lesson = writer_service.write_lesson(topic=request.course_id, knowledge=request.knowledge)
        return lesson
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-lesson", response_model=ReviewResponse)
async def standalone_reviewer(request: ReviewRequest):
    try:
        review_data = reviewer_service.review_lesson(
            topic=request.topic,
            lesson_markdown=request.lesson_markdown,
            review_criteria=request.review_criteria
        )
        return ReviewResponse(**review_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        reply = groq_service.generate(prompt=request.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/structured-chat", response_model=StructuredChatResponse)
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
