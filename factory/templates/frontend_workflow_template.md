# {System Name} — Front-End Workflow

This document describes the front-end generation workflow for {system_name}. It is produced alongside the front-end and serves as a reference for how the UI was generated and how it connects to the backend.

## Inputs

- **system_interface.json**: Tool schemas, workflow ordering, sample data
- **frontend_design.json**: Design configuration (archetype, fonts, palette, content)

## Outputs

- **frontend/**: Complete Next.js application (static export)
- **api/**: FastAPI bridge wrapping each tool as an HTTP endpoint

---

## Step 1: Analyze

The system was analyzed by `factory/tools/analyze_system.py` to produce `system_interface.json`.

### Tools Discovered

| Tool | Arguments | Output Format |
|------|-----------|---------------|
{For each tool: | tool_name | arg1, arg2, ... | json/pdf/csv |}

### Pipeline Order

{Numbered list of tools in execution order from workflow.md}

### Import Safety

{List of any tools flagged as import-unsafe, or "All tools are import-safe."}

---

## Step 2: Design

Design archetype: **Professional SaaS**

- Fonts: {heading_font} + {body_font}
- Palette: {palette_name}
- Layout: Sidebar dashboard with tool form pages

---

## Step 3: API Bridge

Generated endpoints:

| Method | Endpoint | Tool | Response |
|--------|----------|------|----------|
| GET | /api/health | — | JSON status |
{For each tool: | POST | /api/{tool-name} | tool_name | JSON/File |}
| POST | /api/run-pipeline | all tools | JSON steps |

---

## Step 4: Frontend

Generated pages:

| Route | Component | Purpose |
|-------|-----------|---------|
| / | Landing page | Marketing, hero, features |
| /dashboard/ | Dashboard | Tool cards, navigation |
{For each tool: | /dashboard/{tool-slug}/ | Tool form | Input form + result viewer |}
| /dashboard/pipeline/ | Pipeline wizard | Multi-step workflow execution |

---

## Step 5: Deployment

- **Docker**: `docker compose -f docker-compose.frontend.yml up --build`
- **Local dev**: `uvicorn api.main:app --reload` + `cd frontend && npm run dev`
- **Production**: Single container serves API at `/api/*` and static frontend at `/*`
