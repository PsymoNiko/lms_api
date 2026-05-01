# LMS App Server

Django + DRF backend for the LMS platform.

## Tech Stack

- Django 5.2
- Django REST Framework
- JWT auth (`djangorestframework-simplejwt`)
- Django Channels (WebSocket chat + notifications)
- PostgreSQL
- S3-compatible storage via `django-storages` + `boto3`

## Apps

- `accounts`: auth, registration, profile, user management, site-owner overview
- `courses`: course tree, enrollment, grades, messaging, notifications, websocket chat

## Quick Start

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start infrastructure (Postgres + RustFS)

```bash
docker compose up -d
```

### 3) Run migrations

```bash
python manage.py migrate
```

### 4) Run server

```bash
python manage.py runserver
```

Server default: `http://127.0.0.1:8000`

## Seed Demo Data

Populate rich demo users/courses/messages/grades/newsletter:

```bash
python manage.py seed_lms
```

Reset and re-seed:

```bash
python manage.py seed_lms --clear
```

Seed password for all generated users: `seedpass123`

## API Base

All REST routes are under:

- `/api/v1/`

### Public endpoints

- `GET /api/v1/courses/`
- `GET /api/v1/courses/{id}/` (outline for anonymous users)
- `GET /api/v1/stats/`
- `POST /api/v1/newsletter/`
- `POST /api/v1/login/`
- `POST /api/v1/register/`
- `POST /api/v1/auth/register/`
- `POST /api/v1/refresh-token/`

### Authenticated highlights

- `GET /api/v1/me/`
- `GET /api/v1/admin/overview/` (platform admin only)
- `GET /api/v1/enrollments/`
- `POST /api/v1/courses/{id}/enroll/`
- `GET /api/v1/messages/conversations/`
- `GET /api/v1/notifications/`

## WebSocket Chat

Endpoint:

- `ws://127.0.0.1:8000/ws/chat/?token=<access_jwt>`

Supports message send, typing events, read receipts, and live notification push.

## Roles

- `student`
- `instructor`
- `admin`

Use `GET /api/v1/me/` to read access flags for frontend feature gating.

## Important Notes

- `core/settings.py` currently contains development defaults (including `DEBUG=True` and sample DB credentials). Move to environment-based config before production.
- Channel layer is in-memory by default. For production, switch to Redis channel layer.
- Browsable API is enabled only when `DEBUG=True`.

## Documentation

See detailed contracts and checklists in `docs/`:

- `docs/backend-api-contract-fa.md`
- `docs/lms-api-contract.md`
- `docs/frontend-websocket-chat-fa.md`
- `docs/server-api-checklist.md`

