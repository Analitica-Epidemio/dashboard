# Sistema de Epidemiología - Stack Moderno

## Tech Stack
- **Backend**: FastAPI + SQLModel + UV
- **Frontend**: Next.js 15 + TypeScript + TanStack Query
- **Database**: PostgreSQL 16
- **Package Managers**: UV (Python) + PNPM (Node.js)

## Estructura del Proyecto

```
epidemiologia-moderna/
├── backend/          # FastAPI + SQLModel
├── frontend/         # Next.js 15
└── docker-compose.yml
```

## Inicio Rápido

### Backend
```bash
cd backend
uv run dev
```

### Frontend
```bash
cd frontend
pnpm dev
```