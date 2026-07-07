# Kira: Adaptive AI Mock Interview Platform

Kira is a premium, high-fidelity technical mock interview platform designed for students and entry-level developers. It simulates real placement interviews using an adaptive AI voice agent that analyzes resume data, job descriptions, or target company structures to customize topics, ask technical follow-up questions, display code snippets, and evaluate performance dynamically.

---

## 🚀 Key Features

* **High-Fidelity Voice Agent**: Real-time conversational technical interviews powered by LiveKit Agents, combining low-latency streaming STT (Deepgram/AssemblyAI) and TTS (Cartesia/Deepgram/Google).
* **Mock Session Customizer**: Dedicated interview setup wizard offering 5 distinct practice modes:
  * **Resume-Based**: Customizes the adaptive syllabus based on work experiences, academic history, projects, and skills parsed directly from your PDF profile.
  * **Job Description**: Targets and aligns interview topics with pasting target job specifications.
  * **Company Simulator**: Simulates interview structures of popular recruiting presets (e.g. EPAM, Google, Amazon).
  * **Coding Concepts**: Tests data structure selection, algorithmic complexities, and code optimization.
  * **Behavioral Scenario**: Practices project management and communication patterns using the STAR leadership framework.
* **Interactive Code Panel**: Displays code blocks in real time on the frontend corresponding to the active question, prompting candidates to review, optimize, or predict execution behavior.
* **Topic Syllabus Tracker**: Displays a planned visual checklist of the adaptive syllabus showing completed, active, and pending subtopics.
* **Evaluation Dashboard**: High-fidelity session detail summaries detailing:
  * Granular score averages (Technical Accuracy, Communication, Confidence, and Completeness).
  * Qualitative performance review detailing key strengths and areas for improvement.
  * A performance progression graph showing adaptive difficulty shifts over the session.
  * Full transcript review with questions, candidate answers, and evaluator feedback per exchange.

---

## 🛠️ Tech Stack

### Frontend
* **Core**: React 18, TypeScript, Vite
* **Styling**: Tailwind CSS, Shadcn UI, Lucide Icons
* **State Management**: Zustand (local/auth state), React Query (server state synchronization)
* **Analytics**: Recharts (performance progression visualizations)
* **Voice Connection**: `@livekit/components-react` (LiveKit WebRTC audio integration)

### Backend
* **Core**: FastAPI (Python 3.13), Uvicorn
* **Database**: PostgreSQL (SQLAlchemy Async ORM, Alembic migrations)
* **AI & Evaluation**: Gemini API (`gemini-2.5-flash`), LangChain, Pydantic validation schemas
* **Voice Pipeline**: LiveKit Python Agents SDK, Cartesia Sonic voice model, Deepgram STT, AssemblyAI
* **Code Quality**: Ruff (formatting & linting), Pytest (unit & integration testing)

---

## ⚙️ Project Structure

```bash
Kira/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, security, exceptions, and DB engine setups
│   │   ├── models/        # SQLAlchemy model definitions (User, Resume, Interview, etc.)
│   │   ├── repositories/  # Database access repository pattern
│   │   ├── routes/        # FastAPI API routers (auth, interview)
│   │   ├── schemas/       # Pydantic validation schemas
│   │   ├── services/      # Clean architecture business logic services (auth, parser, interview)
│   │   └── agent.py       # LiveKit Voice Agent worker daemon
│   ├── migrations/        # Alembic database migrations
│   ├── tests/             # Pytest test suite
│   ├── pyproject.toml     # Python dependencies & Ruff configuration
│   └── .env.example       # Backend environmental template
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI & Layout components
│   │   ├── hooks/         # Custom server hooks (useAuth, useInterview, etc.)
│   │   ├── lib/           # Fetch clients and utility config wrappers
│   │   ├── pages/         # Page screens (Landing, Setup, Interview, SessionDetails, Profile)
│   │   ├── store/         # Zustand store definitions (authStore)
│   │   └── types/         # TypeScript definitions
│   ├── tailwind.config.js # Tailwind system configuration
│   ├── vite.config.ts     # Vite configuration
│   └── package.json       # Node package manager configurations
└── README.md              # Project documentation
```

---

## 🏁 Getting Started

### Prerequisites
* Python 3.13+
* Node.js 18+
* PostgreSQL Database
* API Credentials:
  * Gemini API Key (Google AI Studio)
  * LiveKit Server (Cloud or self-hosted connection URL, API Key, Secret)
  * Cartesia Voice Key (Sonic model access)
  * STT Access Keys (Deepgram / AssemblyAI)

---

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies using `uv` (recommended) or `pip`:
   ```bash
   uv sync
   ```

3. Create a `.env` file based on `.env.example` and fill out your keys:
   ```env
   # Database Config
   DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/kira

   # JWT Security Config
   JWT_SECRET_KEY=your_jwt_secret_key
   JWT_REFRESH_SECRET_KEY=your_jwt_refresh_key
   COOKIE_SECURE=False

   # Google Gemini API
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-2.5-flash

   # LiveKit Config
   LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
   LIVEKIT_API_KEY=your-api-key
   LIVEKIT_API_SECRET=your-api-secret

   # Agent Gemini Overrides (Optional)
   AGENT_GEMINI_API_KEY=your_agent_gemini_key
   AGENT_GEMINI_MODEL=gemini-2.5-flash

   # STT / TTS providers
   CARTESIA_API_KEY=your_cartesia_key
   ```

4. Run Alembic migrations to initialize the database schema:
   ```bash
   uv run alembic upgrade head
   ```

5. Start the FastAPI development server:
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. Start the LiveKit Voice Agent worker in a separate terminal:
   ```bash
   uv run python -m app.agent dev
   ```

---

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install packages:
   ```bash
   npm install
   ```

3. Create a `.env.local` file and specify the API endpoint:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing & Code Quality

Kira maintains a strict Clean Architecture pattern. Business logic resides in services, endpoints remain thin, and database interactions occur exclusively through repositories.

### Python Code Quality
* **Format & Lint**:
  ```bash
  cd backend
  uv run ruff format .
  uv run ruff check . --fix
  ```
* **Run Tests**:
  ```bash
  uv run pytest
  ```

---

## 🛡️ Reliability Protections

Kira includes built-in safeguards to ensure low latency and session reliability:
* **Zombie Agent Eviction**: Before joining a LiveKit room, the worker uses the LiveKit Server API to proactively identify and kick out ghost processes to prevent double-voice overlays.
* **Row-Level Transaction Locking**: Applies writing row locks (`with_for_update`) during token generations, preventing duplicate concurrent agent dispatches.
* **Rotation Safe Refreshes**: Employs React Query `enabled` state management to coordinate dashboard queries, preventing race conditions from breaking backend token rotation logic.
