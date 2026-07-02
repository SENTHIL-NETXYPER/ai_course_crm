import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.manager import db

client = TestClient(app)

def test_get_courses_endpoint():
    response = client.get("/api/courses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_generate_course_endpoint():
    response = client.post("/api/courses/generate", json={"topic": "Test Course 101", "level": "beginner"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "course" in data
    assert "chapters" in data
    assert isinstance(data["chapters"], list)

def test_standalone_researcher_endpoint():
    response = client.post("/api/research", json={"concept": "Python Variables", "course_id": "python_101"})
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)

def test_standalone_planner_endpoint():
    response = client.post("/api/planner/generate", json={"topic": "Java Programming", "level": "beginner"})
    assert response.status_code == 200
    data = response.json()
    assert "course" in data or "chapters" in data

def test_standalone_organizer_endpoint():
    response = client.post("/api/organize", json={"urls": ["http://example.com/test"]})
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data

def test_standalone_writer_endpoint():
    response = client.post("/api/write-lesson", json={"course_id": "Python", "knowledge": "Variables and loops in python", "quick_mode": True})
    assert response.status_code == 200
    data = response.json()
    assert "chapter" in data or "sections" in data

def test_chat_endpoint():
    response = client.post("/api/chat", json={"message": "Hello AI", "history": []})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
