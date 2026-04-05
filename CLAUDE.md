# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindIQ — Big Five (IPIP-NEO) personality assessment platform for the Indian market. FastAPI backend + Next.js 16 frontend.

## Commands

### Start all services
```bash
bash start_all.sh [dev|stage|prod]   # default: dev
```

### Backend only
```bash
bash backend/deploy_backend.sh [dev|stage|prod]
# Or manually:
conda activate my_good_ipip
cd backend && uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

### Frontend only
```bash
bash frontend/deploy_frontend.sh [dev|stage|prod]
# Or manually:
cd frontend && npm install && npm run dev
```

### Frontend lint
```bash
cd frontend && npm run lint
```

### Frontend production build
```bash
cd frontend && npm run build && npm run start
```

## Environment System

Three environments: `dev`, `stage`, `prod`. Config files in `env/{dev,stage,prod}.env`.

- **dev**: hot reload enabled (uvicorn `--reload`, `next dev`)
- **stage/prod**: no hot reload; backend runs with `--workers 2`, frontend uses `next build && next start`

Deploy scripts auto-generate `backend/.env` and `frontend/.env.local` from the central env file.

## Architecture

### Backend (`backend/`)

FastAPI app at `main.py`. Config via Pydantic Settings in `config.py` (reads `.env`).

**Data flow**: Questions → Submit answers → Score calculation → Payment → AI report generation → PDF

- **Routers** (`routers/`): `assessment`, `payment`, `report` — mounted at `/api/*`
- **Services** (`services/`): `scoring.py` (Big Five 0-100 scale), `ai_report.py` (OpenAI GPT-4o with Indian cultural context), `payment_service.py` (Stripe + mock mode), `pdf_generator.py` (WeasyPrint + Jinja2 templates)
- **Database**: SQLAlchemy 2.0 + SQLite. Single model `Assessment` with JSON fields for answers/scores/percentiles. Sessions via `get_db()` dependency injection.
- **Questions**: 40 IPIP-NEO items (8 per dimension) in `questions/question_bank.py`, some reverse-scored.

API docs auto-generated at `http://localhost:3001/docs`.

### Frontend (`frontend/`)

Next.js 16.2.2 + React 19 + TypeScript + Tailwind CSS 4 + Framer Motion.

- **API client**: `lib/api.ts` — typed fetch wrappers, base URL from `NEXT_PUBLIC_API_URL`
- **User flow**: `/` → `/start` → `/test` → `/analyzing` → `/results` → `/payment` → `/payment/success` → `/report/[id]`
- **Import alias**: `@/*` maps to project root

### Big Five Dimensions

Dimension keys used throughout both frontend and backend: `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`.

## Important Notes

- Next.js 16.2.2 has breaking changes from earlier versions. Read `node_modules/next/dist/docs/` before modifying frontend code. Heed deprecation notices.
- `PAYMENT_MODE=mock` bypasses Stripe in dev. Set to `stripe` with real keys for production.
- No test suite exists yet. No pytest or Jest/Vitest configuration.
- No database migration tooling — `init_db()` creates tables on startup via SQLAlchemy `create_all`.
