# چک‌لیست فشردهٔ بک‌اند ↔ فرانت Next (همین ریپو سرور)

**پایهٔ URL:** `/api/v1/` (یا از طریق پروکسی: `/api-backend/api/v1/`).

## P0 — بدون JWT

| مسیر | وضعیت |
|------|--------|
| `GET /courses/?limit=&offset=` | لیست صفحه‌بندی‌شده؛ فیلدهای کارت شامل `slug`, `thumbnail_url`, `category`, `price`, `instructor_detail` (بدون `email` برای ناشناس). با JWT و **`?mine=1`** فقط دوره‌هایی که **خود کاربر مدرس** است (`admin` / `instructor`). |
| `GET /courses/{id}/` | **بدون JWT / بدون enroll:** فقط متادیتای دوره + **outline** ماژول/درس (`access_level: "outline"`، بدون `contents` و بدون `file_url`). **با JWT** وقتی enroll یا مدرس/ادمین هستید: **درخت کامل** (`access_level: "full"`، `CourseDetail`). |
| `GET /stats/` | `{ courses_count, learners_count, instructors_count }`. |

## P0 — JWT (احراز)

| مسیر | یادداشت |
|------|---------|
| `POST /login/` | SimpleJWT: `{ access, refresh }`. |
| `POST /auth/register/` | همان `RegisterView`؛ بدنه `{ username, email, password, role? }`. |
| `POST /register/` | نام قدیمی؛ معادل همان ثبت‌نام. |
| `POST /refresh-token/` | تازه‌سازی access. |
| `GET/POST/PATCH/DELETE /users/...` | **فقط `admin`** (یا Django superuser). |

**ثبت‌نام عمومی:** از API نمی‌توان نقش **`admin`** ساخت.

## P1 — ثبت‌نام در دوره، لیست enrollment، پیام، نمره

| مسیر | یادداشت |
|------|---------|
| `POST /courses/{id}/enroll/` | Bearer؛ بدنه `{}` OK؛ پاسخ شیء enrollment. |
| `GET /enrollments/` | فقط enrollments کاربر جاری؛ صفحه‌بندی DRF. |
| `GET|POST /messages/` | اختیاری `?course=` روی GET؛ POST: `{ recipient, body, course? }`؛ فیلد `read` (bool) از `read_at`. |
| `GET|PATCH /grades/` | اختیاری `?course=` برای ادمین/مدرس؛ PATCH: `score`, `feedback`, … |

## P1 — CRUD درخت (JWT + مالکیت دوره)

`modules/`, `lessons/`, `contents/` — همان قبلی؛ دانشجو فقط برای دوره‌هایی که enroll شده (یا مدرس/ادمین).

## اختیاری

`POST /newsletter/` — `{ email }`.

## WebSocket چت (real-time)

| موضوع | مسیر / تنظیم |
|--------|----------------|
| اتصال | `ws(s)://<host>/ws/chat/?token=<ACCESS_JWT>` |
| پروتکل JSON | [`frontend-websocket-chat-fa.md`](frontend-websocket-chat-fa.md) |
| Channel layer (پرود) | Redis پیشنهاد می‌شود؛ الان InMemory |

## مدرس: لیست دانشجویان دوره

`GET /api/v1/courses/{id}/students/` — JWT؛ فقط مدرس/ادمین.

## مراجع

- `docs/backend-api-contract-fa.md` — جدول متدها.
- `docs/lms-api-contract.md` / `docs/server-api-checklist.md`.
