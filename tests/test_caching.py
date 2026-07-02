import pytest
from app.database.manager import DatabaseManager

def test_database_manager_caching(tmp_path):
    # Use temporary db path for clean unit testing
    db_file = tmp_path / "test_course_ai.db"
    db = DatabaseManager(db_path=str(db_file))

    # Test saving and retrieving roadmap
    test_roadmap = {
        "id": "python_101",
        "course": "Python 101",
        "chapters": [{"id": 1, "title": "Intro to Python"}]
    }
    db.save_roadmap("python_101", test_roadmap)
    retrieved = db.get_roadmap("python_101")
    assert retrieved is not None
    assert retrieved["course"] == "Python 101"
    assert len(retrieved["chapters"]) == 1

    # Test saving and retrieving chapter lesson
    test_lesson = {
        "chapter": "Intro to Python",
        "introduction": "Welcome to Python programming.",
        "sections": [{"title": "Variables", "content": "x = 10", "order": 1}]
    }
    db.save_lesson("python_101", 1, test_lesson)
    retrieved_lesson = db.get_lesson("python_101", 1)
    assert retrieved_lesson is not None
    assert retrieved_lesson["chapter"] == "Intro to Python"
    assert retrieved_lesson["sections"][0]["content"] == "x = 10"
