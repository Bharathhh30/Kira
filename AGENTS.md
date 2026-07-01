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
- Biome

Before completing any frontend task:

1. Run

npm run format

2. Run

npm run check

3. Run

npm run build

Only finish the task if all commands succeed.

Do not

- use `any`
- use non-null assertions (`!`)
- ignore Biome errors
- disable lint rules

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