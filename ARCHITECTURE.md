# Instagram AI Agent — Architecture

## What This Is

A personal AI agent that helps you decide what to post on Instagram.
Upload a photo → Gemini scores it with numeric edit values → approve it →
Claude generates a caption using RAG from high-engagement posts → copy and post manually.
Agent never touches your feed.

---

## Design Principles

- **Agent advises, human acts** — never posts to Instagram. You copy the caption and post yourself.
- **Photos stay on your machine** — originals never stored. Only scores + metadata in DB.
- **New stack intentionally** — built to learn Gemini vision, Instructor, pgvector, and Celery. Not a copy of the LinkedIn agent.

---

## Stack

| Layer | Tool | Why |
|---|---|---|
| Structured outputs | **Instructor** | Typed Pydantic responses from Claude |
| Vision model | **Gemini 2.5 Flash** | Fast (~3.6s), native structured output via response_schema |
| Caption model | **Claude claude-sonnet-4-6** | Best writing quality |
| Embeddings | **gemini-embedding-001** | 3072d, used for RAG caption retrieval |
| Vector store | **pgvector** | PostgreSQL extension — no separate vector DB |
| Background jobs | **Celery + Redis** | Async photo scoring |
| Backend | **FastAPI** | REST API |
| Frontend | **Next.js + TypeScript + Tailwind** | Single-page upload + results UI |
| Backend hosting | **AWS EC2 t2.micro** | Free tier, Docker Compose |
| Frontend hosting | **Vercel** | Free, auto-deploys from GitHub |

---

## Deployed URLs

- **Frontend**: https://instagram-agent-three.vercel.app
- **Backend**: http://44.198.76.236:8000
- **GitHub**: https://github.com/shreyaspkulkarni/instagram-agent

---

## System Architecture

```
Browser
    │
    │  HTTPS
    ▼
Vercel (Next.js frontend)
    │
    │  Next.js rewrites: /api/backend/* → EC2:8000/*
    │  (server-side proxy — avoids browser mixed content restriction)
    ▼
AWS EC2 t2.micro — Docker Compose
    │
    ├── FastAPI (port 8000)
    │       ├── POST /photos/score       → save temp file, queue Celery task, return job_id
    │       ├── GET  /photos/jobs/{id}   → poll task status (pending/processing/completed)
    │       ├── GET  /photos/            → list all scored photos
    │       ├── PATCH /photos/{id}/status → approve or reject
    │       ├── POST /captions/{photo_id} → RAG + Claude caption generation
    │       ├── GET  /captions/drafts    → list caption drafts
    │       └── GET  /health
    │
    ├── Celery Worker
    │       Picks up tasks from Redis queue
    │       └── score_photo_task: read temp file → Gemini vision → save to DB → delete temp
    │
    ├── PostgreSQL + pgvector (port 5433 local / internal on EC2)
    │
    └── Redis (port 6379)
    │
    ▼
External AI APIs
    ├── Google Gemini API  → gemini-2.5-flash (vision) + gemini-embedding-001 (RAG)
    └── Anthropic API      → Claude claude-sonnet-4-6 (captions via Instructor)
```

---

## User Flow

```
1. Upload photo on the web UI
       ↓
2. FastAPI saves temp file → queues Celery task → returns job_id instantly
       ↓
3. Frontend polls /photos/jobs/{job_id} every 2s
       ↓
4. Celery worker: resize → Gemini scores → save to DB → delete temp
       ↓
5. Score appears: circular gauge, edit values grid (brightness/contrast/etc), AI notes
       ↓
6. User clicks "Approve & Generate Caption"
       ↓
7. Claude + pgvector RAG generates caption + hashtags (~4.4s)
       ↓
8. Caption appears with one-click copy → user pastes into Instagram
```

---

## Photo Intelligence Pipeline

```
POST /photos/score
    │
    ▼
Validate (type + size) → save to photos/temp/{uuid}.jpg → queue task → return job_id
    │
    ▼  (Celery worker, background)
Vision Scorer (backend/vision/scorer.py)
    ├── Resize to 1024px max (Pillow) — critical for speed
    ├── Convert to JPEG, delete temp file
    ├── Gemini 2.5 Flash, thinking_budget=0 (~3.6s)
    └── Returns PhotoScore: score (0–10), composition/lighting/subject notes,
        niche_fit, edit_suggestions (human-readable),
        edit_params (numeric: brightness/contrast/saturation/sharpness/rotation/crop),
        recommended_format, post_worthy
    │
    ▼
Save metadata to PostgreSQL — original photo never stored
```

---

## Caption Pipeline (RAG)

```
POST /captions/{photo_id}
    │
    ▼
Retriever (backend/rag/retriever.py)
    ├── Query: "{niche_fit} {subject_notes}"
    ├── Embed with gemini-embedding-001 (3072d)
    └── Cosine search in pgvector → top 4 high-engagement examples
    │
    ▼
Caption Generator (backend/captions/generator.py)
    ├── Prompt: photo details + 4 RAG examples + common hashtags
    ├── Claude claude-sonnet-4-6 via Instructor
    └── Returns CaptionDraft: caption + hashtags[8–15] + style_notes
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
- Embedded with gemini-embedding-001, stored in `caption_examples` with pgvector

Scripts: `data/scrape_instagram.py` (Apify) → `data/ingest_rag.py` (embed + store)

---

## Edit Params (Numeric, shown in UI)

```python
class EditParams(BaseModel):
    rotation: int       # 0, 90, 180, 270
    brightness: float   # -100 to +100
    contrast: float     # -100 to +100
    saturation: float   # -100 to +100
    sharpness: float    # 0 to 100
    crop_ratio: str     # original | 1:1 | 4:5 | 16:9
```

User applies these manually in Lightroom / VSCO / Photos app.

---

## Database Schema

```sql
users            → single default user (no auth)
photos           → original_filename, score, notes, edit_params (JSONB),
                   recommended_format, post_worthy, status (scored/approved/rejected)
posts            → photo_id FK, caption, hashtags, status (draft/posted)
caption_examples → account, likes, engagement_tier, caption,
                   hashtags (JSONB), embedding vector(3072)
```

---

## Deployment

### EC2 (Backend)
- Instance: t2.micro, Ubuntu 22.04, Elastic IP: 44.198.76.236
- All services run via `docker compose -f docker-compose.prod.yml up -d`
- Services: FastAPI (port 8000) + Celery worker + PostgreSQL + Redis

```bash
# Deploy update
ssh -i ~/Projects/EC2/instagram-agent-key.pem ubuntu@44.198.76.236
cd instagram-agent && git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Vercel (Frontend)
- Repo: github.com/shreyaspkulkarni/instagram-agent
- Root directory: `frontend`
- Env var: `API_URL=http://44.198.76.236:8000`
- Auto-deploys on every push to `main`
- Uses Next.js rewrites to proxy `/api/backend/*` → EC2 (avoids mixed content)

---

## Running Locally

```bash
# Terminal 1 — database + redis
docker compose up -d

# Terminal 2 — backend
uv run uvicorn backend.main:app --port 8000

# Terminal 3 — Celery worker
uv run celery -A backend.celery_app worker --loglevel=info
```

Backend: http://localhost:8000  
API docs: http://localhost:8000/docs  
Frontend: cd frontend && npm run dev → http://localhost:3000

---

## Build Phases

- ✅ Phase 1 — Foundation: Docker + PostgreSQL + FastAPI + Instagram OAuth
- ✅ Phase 2 — Vision Scoring: Gemini 2.5 Flash, thinking_budget=0 (~3.6s), structured EditParams
- ✅ Phase 3 — RAG Data: Apify scraping (50 posts), gemini-embedding-001, pgvector ingestion
- ✅ Phase 4 — Caption Generation: Claude claude-sonnet-4-6 + Instructor + RAG (~4.4s)
- ✅ Phase 5 — Async Jobs: Celery + Redis, job polling, solo pool for macOS
- ✅ Phase 6 — Frontend: Next.js dark UI, score ring, edit values grid, caption + copy
- ✅ Phase 7 — Deploy: AWS EC2 t2.micro + Docker Compose + Vercel + Next.js proxy rewrite

---

## What This Demonstrates

| Skill | Where it shows |
|---|---|
| Multimodal AI (vision) | Gemini 2.5 Flash scoring photos with native structured output |
| RAG pipeline | Scrape → embed → pgvector → retrieve → Claude generate |
| pgvector | Cosine similarity search, no separate vector DB |
| Structured LLM outputs | Instructor + Pydantic for caption generation |
| Async background jobs | Celery + Redis, job polling, macOS fork safety |
| Full-stack | FastAPI + Next.js + Tailwind |
| AWS deployment | EC2 t2.micro, Docker Compose, Elastic IP |
| Vercel deployment | Auto-deploy from GitHub, server-side proxy rewrites |
| Google Gemini API | Vision scoring + embeddings |
| Anthropic Claude API | RAG-augmented caption generation |
