---
title: StudyMind AI Backend
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# StudyMind AI — Backend API

FastAPI backend for the StudyMind AI study assistant platform.

## API URL

Once deployed, your API will be available at:

```
https://<your-hf-username>-studymind-ai-backend.hf.space
```

Use this URL as the `NEXT_PUBLIC_API_URL` in your Next.js frontend `.env`:

```env
NEXT_PUBLIC_API_URL=https://<your-hf-username>-studymind-ai-backend.hf.space
```

## Features

- **JWT Authentication** — Register, login, token refresh
- **Study Sessions** — Create and manage study sessions per subject
- **AI Chat** — Real-time streaming responses via Gemini AI
- **Sentiment Analysis** — Track student engagement and emotional state
- **Progress Tracking** — XP, streaks, levels, and study time
- **Voice Input** — Audio transcription via Gemini multimodal
- **WebSocket Support** — Real-time chat via WebSocket connections

## Environment Variables

Set these as **Secrets** in your HF Space settings:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (NeonDB) |
| `JWT_SECRET` | 64-char hex secret for JWT signing |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Model name (default: `gemini-1.5-flash`) |
| `CORS_ORIGIN` | Frontend URL (e.g. `https://your-app.vercel.app`) |

## Local Development

```bash
# Install dependencies
uv sync

# Run dev server
uv run uvicorn app.main:app --reload --port 7860

# Run tests
uv run pytest -v
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login (returns JWT tokens) |
| `GET` | `/auth/me` | Get current user profile |
| `GET` | `/subjects` | List all subjects |
| `POST` | `/subjects` | Create a subject |
| `POST` | `/sessions` | Start a study session |
| `GET` | `/sessions` | List user sessions |
| `GET` | `/sessions/{id}` | Get session details |
| `WS` | `/ws/study/{id}` | WebSocket chat endpoint |
| `GET` | `/health/` | Health check |

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL (NeonDB) + SQLAlchemy async
- **AI**: Google Gemini API
- **Auth**: JWT (PyJWT + bcrypt)
- **Deployment**: Hugging Face Spaces (Docker)

---

## Author

Built by **Ifiezibe Samuel** — [GitHub](https://github.com/thetruesammyjay)
