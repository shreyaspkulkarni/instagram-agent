# Instagram AI Agent

## What This Project Is
A personal AI agent that helps decide what to post on Instagram.
Upload photos → agent scores them with Gemini vision, suggests edits, generates
captions in your voice using RAG. You post manually — agent never touches your feed.

Intentionally uses a different stack from the LinkedIn agent to learn new tools:
CrewAI, Gemini 2.0 Flash, Instructor, pgvector, Celery + Redis.

## Stack
- **Agent framework:** CrewAI (multi-agent with specialized roles)
- **Structured outputs:** Instructor (typed Pydantic responses from LLMs)
- **Vision:** Google Gemini 2.0 Flash (~$0.0003/photo)
- **Caption gen:** Claude claude-sonnet-4-6 (best writing quality)
- **Vector store:** pgvector (PostgreSQL extension — no Pinecone)
- **Background jobs:** Celery + Redis (async photo processing)
- **Image editing:** Pillow + rawpy
- **Backend:** Python FastAPI
- **Frontend:** Next.js + TypeScript + Tailwind (Phase 7)
- **Auth:** Instagram Graph API OAuth 2.0 (Creator account, read-only scopes)
- **DB:** PostgreSQL port 5433 locally (avoids conflict with LinkedIn agent on 5432)

## CrewAI Agents
1. **Content Strategist** — decides what to post this week, synthesizes all inputs
2. **Photo Scorer** — scores uploaded photos using Gemini vision (0–10 + edit notes)
3. **Caption Writer** — generates captions + hashtags using pgvector RAG
4. **Trend Researcher** — finds trending topics/hashtags using Tavily

## What the Agent Does NOT Do
- Post to Instagram (user posts manually)
- Schedule posts
- Store original photos (originals stay on user's Mac, only metadata in DB)

## Key Files
- `ARCHITECTURE.md` — full system design, CrewAI crew, DB schema, build phases
- `backend/main.py` — FastAPI app
- `backend/config.py` — Pydantic settings from .env
- `backend/instagram/auth.py` — OAuth (read-only scopes only)
- `backend/db/models.py` — DB models
- `backend/db/crud.py` — DB operations

## Checkpoints
- ✅ Checkpoint 1 (Phase 1 complete): Docker + PostgreSQL + FastAPI + Instagram OAuth working. JWT confirmed. User saved to DB (username: iamshreyasss).
- ✅ Checkpoint 2 (Phase 2 complete): Gemini 2.5 Flash vision scoring working. Native google-genai SDK (thinking_budget=0 — 3.6s response). Instructor dropped for vision, replaced with native structured output via response_schema. Photo resize pipeline (Pillow, 1024px). /photos/score endpoint stores metadata in DB.
- ✅ Checkpoint 3 (Phases 3+4 complete): pgvector RAG working. Scraped 50 high-engagement posts (5 accounts, top 10 each) via Apify, embedded with gemini-embedding-001 (3072d), stored in pgvector. Claude claude-sonnet-4-6 + Instructor generates captions in ~4.4s using RAG examples. POST /captions/{photo_id} and GET /captions/drafts endpoints working.
- ✅ Checkpoint 4 (Phase 5 complete): Celery + Redis async job queue. POST /photos/score now returns job IDs instantly (<100ms). Celery worker scores photos in background (~3.6s). Poll GET /photos/jobs/{job_id} for status. Redis added to Docker.

## Vision Model Notes
- Only gemini-2.5-flash is available for new Google AI Studio users (2.0 and 1.5 models deprecated)
- Must use native google-genai SDK — OpenAI-compatible endpoint doesn't support thinking_config
- thinking_budget=0 is critical — without it gemini-2.5-flash takes 600s (thinking mode)

## Current Phase
Phase 5 complete. Next: Phase 6 — Pillow editing pipeline (apply EditParams to photos).

## Instagram API Notes
- Read-only scopes: `instagram_business_basic`, `instagram_business_manage_comments`
- App in Development mode — only testers can authenticate
- Redirect URI requires HTTPS — use ngrok for local dev
- Run uvicorn WITHOUT --reload (OAuth state is in-memory)
- Long-lived tokens expire 60 days

## Dev Setup
```bash
cp .env.example .env
# fill in: INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, SECRET_KEY,
#          ANTHROPIC_API_KEY, GOOGLE_API_KEY

# Terminal 1
docker compose up -d

# Terminal 2 (no --reload)
uv run uvicorn backend.main:app --port 8000

# Terminal 3 (HTTPS for OAuth redirect)
ngrok http 8000
```

Backend: http://localhost:8000
API docs: http://localhost:8000/docs
