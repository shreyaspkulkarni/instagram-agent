# Instagram AI Agent — Architecture

## What This Is

A personal AI agent that helps you decide what to post on Instagram.
You upload photos → it scores them with Gemini vision, suggests numeric edits,
generates captions using RAG from high-engagement posts. You post manually.
Agent never touches your feed.

Not a chatbot. A FastAPI backend with specialized AI pipelines — Gemini vision,
pgvector RAG, Claude caption generation, and a Pillow editing pipeline.

---

## Design Principles

- **Agent advises, human acts** — agent never posts to Instagram. You copy the caption, grab the edited photo, post yourself.
- **Photos stay on your machine** — originals never uploaded to any cloud storage. Only scores + metadata stored in DB.
- **New stack intentionally** — built to learn CrewAI, Gemini vision, Instructor structured outputs, pgvector, and Celery. Not a copy of the LinkedIn agent.

---

## Stack

| Layer | Tool | Why |
|---|---|---|
| Agent framework | **CrewAI** | Multi-agent with specialized roles (Phase 6) |
| Structured outputs | **Instructor** | Typed Pydantic responses from Claude |
| Vision model | **Gemini 2.5 Flash** | Fast (~3.6s), native structured output via response_schema |
| Caption model | **Claude claude-sonnet-4-6** | Best writing quality |
| Embeddings | **gemini-embedding-001** | 3072d, used for RAG caption retrieval |
| Vector store | **pgvector** | PostgreSQL extension — no separate vector DB |
| Background jobs | **Celery + Redis** | Async photo processing (Phase 5) |
| Image editing | **Pillow** | Crop, exposure, sharpen (Phase 6) |
| Backend | **FastAPI** | REST API |
| Frontend | **Next.js + TypeScript** | Photo grid + caption editor (Phase 7) |

---

## System Architecture

```
Next.js Frontend (localhost:3000 → Vercel in prod)
    │
    │  HTTPS via axios
    ▼
FastAPI Backend (localhost:8000 → AWS EC2 in prod)
    │
    ├── /auth/instagram/login         → Instagram OAuth redirect
    ├── /auth/instagram/callback      → exchange code, store user + JWT
    ├── /photos/score                 → upload photos, queue Celery tasks, return job IDs
    ├── /photos/jobs/{job_id}         → poll scoring job status (pending/processing/completed)
    ├── /photos/                      → list all scored photos (filter by status)
    ├── /photos/{id}/status           → approve or reject a scored photo
    ├── /captions/{photo_id}          → generate caption for approved photo (RAG + Claude)
    ├── /captions/drafts              → list all caption drafts
    └── /health                       → health check
    │
    ├── Celery Worker (separate process)
    │       Picks up tasks from Redis queue
    │       └── score_photo_task: read temp file → Gemini vision → save to DB → delete temp
    │
    ▼
AI Pipelines
    ├── Vision Pipeline (Gemini 2.5 Flash)
    │       Resize to 1024px → Gemini vision → PhotoScore (Pydantic) → store in DB
    │
    └── Caption Pipeline (pgvector RAG + Claude claude-sonnet-4-6)
            Embed query → cosine search caption_examples → top 4 examples
            → Claude + Instructor → CaptionDraft (Pydantic) → store as Post draft
    │
    ▼
External Services
    ├── Instagram Graph API  → OAuth, profile read only (Creator account)
    ├── Google Gemini API    → gemini-2.5-flash vision + gemini-embedding-001
    ├── Anthropic API        → Claude claude-sonnet-4-6 for caption generation
    ├── PostgreSQL + pgvector → structured data + vector similarity search
    └── Redis               → Celery broker + result backend
```

---

## Photo Intelligence Pipeline

```
User uploads photo via POST /photos/score
    │
    ▼
FastAPI route
    ├── Validate file type + size
    ├── Save bytes to photos/temp/{uuid}.jpg
    └── Queue score_photo_task → return job_id immediately (<100ms)
    │
    ▼
Celery Worker (background)
    │
    ▼
Vision Scorer (backend/vision/scorer.py)
    ├── Resize to 1024px max (Pillow) — keeps Gemini calls fast
    ├── Convert to JPEG, delete temp file
    ├── Send to gemini-2.5-flash with thinking_budget=0 (~3.6s)
    ├── Native structured output via response_schema=PhotoScore
    └── Returns: score (0–10), composition/lighting/subject notes,
               niche_fit, edit_suggestions (human), edit_params (machine),
               recommended_format, post_worthy
    │
    ▼
PostgreSQL photos table
    └── Stores all metadata — original stays on user's Mac
    │
    ▼
User polls GET /photos/jobs/{job_id} → pending / processing / completed
User reviews score → PATCH /photos/{id}/status → approved or rejected
    │
    ▼  (if approved)
Caption Pipeline → see below
```

---

## Caption Pipeline (RAG)

```
POST /captions/{photo_id}
    │
    ▼
Retriever (backend/rag/retriever.py)
    ├── Build query: "{niche_fit} {subject_notes}"
    ├── Embed with gemini-embedding-001 (3072d)
    ├── Cosine similarity search in pgvector caption_examples table
    └── Return top 4 examples with account, likes, engagement_tier, caption, hashtags
    │
    ▼
Caption Generator (backend/captions/generator.py)
    ├── Build prompt: photo details + 4 high-engagement examples + common hashtags
    ├── Call Claude claude-sonnet-4-6 via Instructor (structured output)
    └── Returns: CaptionDraft(caption, hashtags[8–15], style_notes)
    │
    ▼
Save as Post draft → PostgreSQL posts table
```

---

## RAG Seed Data

50 high-engagement posts scraped from 5 Instagram accounts via Apify:

| Account | Niche |
|---|---|
| joshuacoppen | lifestyle/travel |
| mencrucials | men's fashion |
| alexcosta | men's style/grooming |
| rohit_khandelwal77 | fitness/lifestyle |
| sankett25 | lifestyle |

- Top 10 images per account by engagement
- 23 VIRAL + 27 HIGH engagement tier posts
- Embedded with gemini-embedding-001, stored in `caption_examples` table with pgvector

Scripts: `data/scrape_instagram.py` (Apify) → `data/ingest_rag.py` (embed + store)

---

## Database Schema

```sql
users               → Instagram identity, JWT access token, token expiry
user_memory         → key/value store for agent's persistent memory
instagram_profiles  → bio, followers, avg engagement, best posting times, niche tags
photos              → original_filename, score, composition/lighting/subject notes,
                      niche_fit, edit_suggestions (JSONB), edit_params (JSONB),
                      recommended_format, post_worthy, status (scored/approved/rejected)
posts               → photo_id FK, caption, hashtags, status (draft/posted)
conversations       → full chat history (role + content + tool_calls)
caption_examples    → account, likes, comments, engagement_tier, caption,
                      hashtags (JSONB), embed_text, embedding vector(3072)
```

---

## Edit Params (Machine-Readable)

Vision scorer returns structured `EditParams` consumed by the Pillow pipeline (Phase 6):

```python
class EditParams(BaseModel):
    rotation: int       # 0, 90, 180, 270
    brightness: float   # -100 to +100
    contrast: float     # -100 to +100
    saturation: float   # -100 to +100
    sharpness: float    # 0 to 100
    crop_ratio: str     # original | 1:1 | 4:5 | 16:9
```

---

## Frontend Pages (Phase 7)

```
/                    → Login (Instagram OAuth)
/auth/callback       → Token handler
/photos              → Upload photos, scored grid, filter by score, approve/reject
/drafts              → Caption drafts — editor, copy to clipboard for posting
```

---

## Instagram API Notes

- Requires **Creator or Business account** (not personal)
- OAuth scopes used (read-only):
  - `instagram_business_basic` — profile + media read
  - `instagram_business_manage_comments` — comment read
- Long-lived tokens expire in 60 days — refresh needed in production
- App must be in **Live mode** for non-tester accounts
- Run uvicorn **without --reload** — OAuth state is in-memory

---

## Environment Variables

```
# Instagram / Meta
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_REDIRECT_URI=https://<ngrok>.ngrok-free.app/auth/instagram/callback

# Anthropic
ANTHROPIC_API_KEY=

# Google
GOOGLE_API_KEY=

# Apify (one-time scraping)
APIFY_API_TOKEN=

# PostgreSQL (port 5433 — avoids conflict with LinkedIn agent on 5432)
DATABASE_URL=postgresql://instagram_agent:password@localhost:5433/instagram_agent

# App
SECRET_KEY=
FRONTEND_URL=http://localhost:3000
```

---

## Running Locally

```bash
# Terminal 1 — database + redis
docker compose up -d

# Terminal 2 — backend (no --reload, OAuth state is in-memory)
uv run uvicorn backend.main:app --port 8000

# Terminal 3 — Celery worker
uv run celery -A backend.celery_app worker --loglevel=info

# Terminal 4 — HTTPS for OAuth redirect
ngrok http 8000
```

Backend: http://localhost:8000
API docs: http://localhost:8000/docs

---

## Build Phases

- ✅ Phase 1 — Foundation: Docker + PostgreSQL + FastAPI + Instagram OAuth + JWT
- ✅ Phase 2 — Vision Scoring: Gemini 2.5 Flash (thinking_budget=0, 3.6s), structured EditParams, /photos/score endpoint
- ✅ Phase 3 — RAG Data: Apify scraping (50 posts), gemini-embedding-001, pgvector ingestion
- ✅ Phase 4 — Caption Generation: Claude claude-sonnet-4-6 + Instructor + RAG, /captions/{photo_id} endpoint
- ✅ Phase 5 — Async Jobs: Celery + Redis. /photos/score queues tasks, returns job IDs immediately. Worker scores in background (~3.6s). Poll /photos/jobs/{job_id} for status.
- ⬜ Phase 6 — Editing Pipeline: Pillow applies EditParams (crop, brightness, contrast, sharpen)
- ⬜ Phase 7 — Frontend: Next.js photo grid + caption editor
- ⬜ Phase 8 — Deploy: AWS EC2 + RDS + Vercel

---

## What This Demonstrates

| Skill | Where it shows |
|---|---|
| Multimodal AI (vision) | Gemini 2.5 Flash scoring photos with structured output |
| RAG pipeline | Scrape → embed → pgvector → retrieve → Claude generate |
| pgvector | Cosine similarity search, no separate vector DB needed |
| Structured LLM outputs | Instructor + Pydantic for both vision and caption generation |
| Image processing | Pillow resize pipeline, EditParams for Pillow ops |
| Instagram Graph API | OAuth, read-only, Creator account |
| Full-stack (FastAPI + Next.js) | REST API + React frontend (Phase 7) |
| PostgreSQL + SQLAlchemy | Relational DB with proper models |
| Anthropic Claude API | Caption generation, RAG-augmented, Instructor structured output |
| Google Gemini API | Vision scoring + embeddings |
