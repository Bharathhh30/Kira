# Kira Development Guide

## General Rules

- Never bypass CI.
- Never disable lint rules unless explicitly instructed.
- Prefer small, modular components.
- Prefer composition over large files.
- Write readable TypeScript and Python.
- Follow existing project structure.
- If adding a dependency, explain why.

## Frontend

Stack
- React
- TypeScript
- Vite
- Tailwind CSS
- Zustand
- Shadcn

Always

- organize imports
- use accessible HTML
- use semantic components
- keep components small

## Backend

Stack

- FastAPI
- Python 3.13
- Ruff
- Pytest
- Pydantic
- Sqlalchemy
- Postgres
- Docker
- Redis
- Alembic
- Langchain
- Langgraph
- Livekit agents

Before completing any backend task:

ruff format .
ruff check .
pytest

Only finish when all commands pass.

Always

- use type hints
- keep routes thin
- move business logic into services
- validate inputs with Pydantic

## Definition of Done

A task is complete only if

- project builds
- lint passes
- tests pass
- no new warnings introduced
- code follows project architecture

## Architecture Rules

- This project follows Clean Architecture.
- Business logic belongs inside services.
- Routes should remain thin.
- Agents never access the database directly.
- All persistence happens through repositories.

## Coding Rules

- No business logic in routes.
- No SQL inside endpoints.
- Use async everywhere possible.
- Always type hint.
- Use Pydantic schemas.
- One responsibility per service.

## Database Rules

- Never delete interviews.
- Soft delete users.
- Always use UUID.
- Never store passwords.
- Refresh tokens must be hashed.

## Frontend Rules

- React Query for server state.
- Zustand for local state.
- No API calls inside components.
- Use hooks.
- UI is dumb.
- Business logic lives in hooks.