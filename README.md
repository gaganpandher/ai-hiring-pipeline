# 🧠 AI Hiring Pipeline with Bias Detection

A full-stack, event-driven hiring platform showcasing:
- **MySQL** — normalised relational schema with complex analytical queries
- **FastAPI (Python)** — async REST API with JWT auth and RBAC
- **Apache Kafka** — 6 real-time event topics
- **React + TypeScript** — multi-portal frontend with analytics dashboard
- **Redis** — session caching and rate limiting
- **AI Services** — resume scoring and statistical bias detection

---

## 🗂️ Project Structure

```
ai-hiring-pipeline/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # config, database, redis, kafka, security
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic
│   │   └── consumers/    # Kafka consumer workers
│   ├── alembic/          # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios client + API hooks
│   │   ├── components/   # Shared UI components
│   │   ├── pages/        # Route-level pages
│   │   ├── store/        # Zustand state stores
│   │   └── hooks/        # Custom React hooks
│   ├── package.json
│   └── Dockerfile
├── docker/
│   └── mysql/init.sql
├── scripts/
│   └── setup.sh
├── docker-compose.yml
└── .env
```

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose v2
- (Optional) Node 20+ and Python 3.11+ for local dev without Docker

### 1. Clone and configure
```bash
git clone <repo-url>
cd ai-hiring-pipeline
cp .env .env.local   # edit secrets if needed
```

### 2. Run the setup script
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Access the services
| Service         | URL                              |
|-----------------|----------------------------------|
| React App       | http://localhost:3000            |
| FastAPI Docs    | http://localhost:8000/api/docs   |
| Kafka UI        | http://localhost:8080            |
| MySQL           | localhost:3306                   |
| Redis           | localhost:6379                   |

---

## 🔧 Local Development (without Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Set local DATABASE_URL pointing to your MySQL
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev    # starts on http://localhost:3000
```

---

## 🏗️ Architecture

```
React (port 3000)
    ↓ HTTP (Vite proxy)
FastAPI (port 8000)
    ├── MySQL  — persistent relational data
    ├── Redis  — JWT sessions, caching
    └── Kafka  — event streaming
            ├── applications         ← new job submissions
            ├── scoring-results      ← AI resume scores
            ├── bias-alerts          ← statistical bias flags
            ├── audit-log            ← immutable decision trail
            ├── notifications        ← email/webhook triggers
            └── recruiter-actions    ← hire / reject events
```

---

## 👤 User Roles

| Role        | Capabilities                                            |
|-------------|--------------------------------------------------------|
| `admin`     | Full access, bias reports, user management             |
| `recruiter` | Post jobs, review applications, make decisions         |
| `applicant` | Browse jobs, submit applications, track status         |

---

## 📊 Key Features

- **AI Resume Scoring** — spaCy NLP + sklearn scoring model
- **Bias Detection** — χ² statistical test on recruiter decisions
- **Real-time Dashboard** — Recharts analytics via Kafka event stream
- **Audit Trail** — every decision logged immutably to Kafka
- **RBAC** — JWT + role-based route guards on both frontend and backend
