# Course AI — AI-Powered Course Generator

An intelligent, multi-agent course generation platform that builds complete course textbooks from scratch using an orchestrated pipeline of AI agents.

---

## ✨ Features

- 🧠 **Multi-Agent Architecture** — Planner → Researcher → Scraper → Organizer → Writer → Reviewer pipeline
- 📚 **Full Course Compilation** — Generates entire textbooks chapter-by-chapter automatically
- ⚡ **Smart Caching** — SQLite database prevents redundant AI calls; cache-hits serve instantly
- 🔄 **Self-Reflection Loop** — Writer agent iterates on reviewer feedback up to 3 times before saving
- 🌐 **REST API-First Design** — Every agent is independently testable via Swagger UI (`/docs`)
- 🎨 **Immersive Frontend** — React reader interface with dark mode, animations, and live agent status

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| AI / LLM | Groq (Llama 3.3) |
| Database | SQLite via Python `sqlite3` |
| Scraping | BeautifulSoup + httpx |
| Frontend | React (CDN) + Vanilla CSS |
| Logging | Loguru |

---

## 🚀 Quick Start (Local)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/course-ai.git
cd course-ai
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.  
Swagger docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key from [console.groq.com](https://console.groq.com) |

---

## 📡 API Reference

The full REST API follows a modular-first testing design:

```
POST /courses/generate      → Planner Agent creates course roadmap
GET  /courses/{course_id}   → Fetch course syllabus + chapter list
POST /chapters/{id}/generate → Compile a chapter (Research → Write → Review)
GET  /chapters/{id}         → Read compiled lesson content
```

### Standalone Agent Endpoints (for isolated testing)

```
POST /planner/generate      → Test the Planner Agent alone
POST /research              → Test the Researcher Agent alone
POST /scrape                → Test the Scraper Service alone
POST /organize              → Test the Organizer Agent alone
POST /write-lesson          → Test the Writer Agent alone
POST /review-lesson         → Test the Reviewer Agent alone
```

Full interactive docs: `http://localhost:8000/docs`

---

## 🧱 Project Structure

```
course-ai/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── api/
│   │   └── routes.py           # All REST endpoints
│   ├── agents/
│   │   ├── planner/            # Planner Agent (course syllabus)
│   │   ├── researcher/         # Researcher Agent (web search)
│   │   ├── organizer/          # Organizer Agent (knowledge building)
│   │   ├── writer/             # Writer Agent (lesson drafting)
│   │   └── reviewer/           # Reviewer Agent (critique & refinement)
│   ├── services/
│   │   ├── groq_service.py     # Groq LLM client wrapper
│   │   └── scrape_service.py   # Web scraper (httpx + BeautifulSoup)
│   ├── database/
│   │   └── manager.py          # SQLite cache (roadmaps + lessons)
│   ├── schemas/                # Pydantic request/response models
│   ├── prompts/                # Prompt templates for each agent
│   └── static/
│       └── index.html          # React frontend (single-page app)
├── data/                       # SQLite DB + scraped content (gitignored)
├── tests/                      # Test suite
├── .env.example                # Environment variable template
├── .gitignore
├── Procfile                    # For Heroku/Railway/Render hosting
├── requirements.txt
└── README.md
```

---

## ☁️ Hosting on Render (Free Tier)

1. Push code to a GitHub repository.
2. Go to [render.com](https://render.com) → **New Web Service**.
3. Connect your GitHub repo.
4. Set the following:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add `GROQ_API_KEY`
5. Click **Deploy**.

> ⚠️ **Note**: SQLite is ephemeral on Render's free tier. For production persistence, migrate to **PostgreSQL** (Supabase or Render's managed DB).

---

## ☁️ Hosting on Railway

1. Install the [Railway CLI](https://docs.railway.app/develop/cli): `npm install -g @railway/cli`
2. Login: `railway login`
3. Deploy: `railway up`
4. Set env vars in the Railway dashboard.

---

## 🧪 Testing the API

### Modular Testing Order (correct sequence)
```bash
# 1. Generate course roadmap
curl -X POST http://localhost:8000/courses/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python", "level": "beginner"}'

# 2. Get course syllabus
curl http://localhost:8000/courses/python

# 3. Compile a chapter
curl -X POST http://localhost:8000/chapters/1/generate \
  -H "Content-Type: application/json" \
  -d '{"course_id": "python", "regenerate": false}'

# 4. Read compiled lesson
curl "http://localhost:8000/chapters/1?course_id=python"
```

---

## 📄 License

MIT License — feel free to fork, extend, and deploy.
