# Course AI API Documentation

This backend is designed as an agentic system that generates complete courses. It consists of multiple independent agents collaborating to build a syllabus, gather data, organize content, draft lessons, and review them.

FastAPI automatically generates interactive Swagger API docs at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Endpoint Specifications

### 1. Welcome / Health Check
- **Endpoint**: `GET /`
- **Description**: Verifies the API server is active.
- **Response**:
  ```json
  {
    "message": "Welcome to Course AI API!"
  }
  ```

### 2. Planner Agent
- **Endpoint**: `POST /api/generate-roadmap`
- **Description**: Generates high-level learning chapters for a given course topic.
- **Request Body**:
  ```json
  {
    "topic": "Python",
    "audience": "beginner"
  }
  ```
- **Response Body**:
  ```json
  {
    "course": "Python",
    "chapters": [
      {
        "title": "Introduction to Python",
        "description": "Getting started with the basic syntax and core principles of Python.",
        "order": 1
      },
      ...
    ]
  }
  ```

### 3. Researcher Agent
- **Endpoint**: `POST /api/research`
- **Description**: Uses DuckDuckGo to search for specific concepts and outputs relevant tutorial and resource URLs.
- **Request Body**:
  ```json
  {
    "topic": "Python",
    "concept": "Variables"
  }
  ```
- **Response Body**:
  ```json
  {
    "topic": "Python",
    "concept": "Variables",
    "urls": [
      "https://www.w3schools.com/python/python_variables.asp",
      "https://www.geeksforgeeks.org/python/python-variables/"
    ]
  }
  ```

### 4. Content Scraper
- **Endpoint**: `POST /api/scrape`
- **Description**: Scrapes a webpage, strips out navigation and script clutter, translates the HTML content into clean markdown, and saves it locally in the `data/scraped` directory.
- **Request Body**:
  ```json
  {
    "url": "https://www.w3schools.com/python/python_variables.asp"
  }
  ```
- **Response Body**:
  ```json
  {
    "success": true,
    "saved_filename": "www_w3schools_com_python_python_variables_asp.md",
    "markdown_snippet": "Python Variables..."
  }
  ```

### 5. Organizer Agent
- **Endpoint**: `POST /api/organize`
- **Description**: Merges content blocks from multiple scraped URLs, deletes duplicated information, and organizes the distinct concepts into clean learning categories.
- **Request Body**:
  ```json
  {
    "urls": [
      "https://www.w3schools.com/python/python_variables.asp"
    ]
  }
  ```
- **Response Body**:
  ```json
  {
    "categories": [
      {
        "name": "Variables and Data Types",
        "description": "Fundamental ways to store and represent data in Python.",
        "topics": [
          {
            "title": "Variable Declaration",
            "summary": "Variables are containers created the moment you assign a value to them using the assignment operator (=)."
          },
          ...
        ]
      }
    ]
  }
  ```

### 6. Writer Agent
- **Endpoint**: `POST /api/write-lesson`
- **Description**: Compiles educational content in markdown format based on organized source knowledge and a style template.
- **Request Body**:
  ```json
  {
    "topic": "Python Variables",
    "knowledge": "Variables in Python are dynamically typed. You declare them by assignment (e.g. x = 5). Names are case sensitive.",
    "style_template": "Format as standard clean Markdown, include clear section headings, explanations, and Python code blocks."
  }
  ```
- **Response Body**:
  ```json
  {
    "topic": "Python Variables",
    "lesson_markdown": "# Python Variables\n\nWelcome to the lesson on Python Variables! In this lesson, we will cover..."
  }
  ```

### 7. Reviewer Agent
- **Endpoint**: `POST /api/review-lesson`
- **Description**: Performs a rigorous critique of the drafted lesson content, check rules (spelling, formatting, syntax), and generates refined markdown if necessary.
- **Request Body**:
  ```json
  {
    "topic": "Python Variables",
    "lesson_markdown": "# Python Variables\n\nWelcome to Python Variables.",
    "review_criteria": "Verify python syntax is correct, spelling/grammar is correct, formatting is clean, and explanation is clear."
  }
  ```
- **Response Body**:
  ```json
  {
    "approved": true,
    "feedback": "The lesson structure is excellent. Code snippets are accurate and clear. No grammatical or layout errors found. Approving content.",
    "refined_markdown": "# Python Variables\n\nWelcome to the lesson on Python Variables! In this lesson, we will cover..."
  }
  ```
