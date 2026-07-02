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
