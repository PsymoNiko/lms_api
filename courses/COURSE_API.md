# LMS Course API — spec for frontend / AI

Base URL: same origin as the Django server (e.g. `http://127.0.0.1:8000`).  
All paths below are prefixed with **`/api/v1/`**.

## Authentication

- **JWT** (same as accounts): send header  
  `Authorization: Bearer <access_token>`
- **Default**: endpoints require an authenticated user unless noted below.
- **Public (no JWT)**:
  - **`GET /api/v1/courses/`** — for landing / catalog.
  - **`GET /api/v1/courses/{id}/`** — **Without enrollment:** metadata + syllabus **outline** only (`access_level: "outline"`, lessons **without** `contents`). **Full** `CourseDetail` (with `contents`, `file_url`) when `access_level: "full"` (enrolled learner, course instructor, or `admin`).
  - **`GET /api/v1/stats/`** — aggregate counts.
  - **`POST /api/v1/newsletter/`** — email capture (throttled).
- **Roles**: `admin` | `instructor` | `student` (on `CustomUser`).
- **Writes** (POST / PUT / PATCH / DELETE): only **`admin`** or the **course instructor** (`course.instructor`) for that resource’s course (courses + nested resources).
- **Reads** for **modules / lessons / contents**: authenticated users only (unchanged).
- **`instructor_detail`**: when the caller is **not** logged in, **`email` is omitted** from each instructor object.
- **Create course**: **`student` is rejected**. **`instructor`**: omit `instructor` in body → you become instructor. **`admin`**: must send `instructor` (user id).
- **Instructor / admin course list**: with JWT, **`GET /api/v1/courses/?mine=1`** returns only courses where the current user is **`instructor`** (ignored for students).
- **User management**: **`/api/v1/users/`** (CRUD) is **`IsPlatformAdmin`** only — JWT user with **`role === "admin"`** or Django superuser. Public register endpoints cannot create **`admin`** (`RegisterSerializer`).

---

## Pagination (list responses)

DRF **limit/offset** (from project settings):

- Query: `?limit=50&offset=0`
- Response shape typically includes `count`, `next`, `previous`, `results` (array).

---

## Data models (TypeScript-style)

Use these types in the frontend; datetime fields are **ISO 8601 strings** from the API.

```ts
type UserRole = "admin" | "instructor" | "student";

/** When unauthenticated, `email` may be absent. */
interface UserBrief {
  id: number;
  username: string;
  email?: string;
  role: UserRole;
}

type LessonContentType = "text" | "video" | "audio" | "document";

interface Course {
  id: number;
  title: string;
  slug: string;
  description: string;
  thumbnail: string | null; // write path; read may be storage URL
  thumbnail_url: string | null; // read-only absolute URL when image exists
  category: string;
  price: string; // decimal as string, e.g. "0.00"
  instructor: number; // FK user id
  instructor_detail: UserBrief;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

interface Module {
  id: number;
  course: number; // FK course id
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

interface Lesson {
  id: number;
  module: number; // FK module id
  title: string;
  content_type: LessonContentType;
  created_at: string;
  updated_at: string;
}

/** Full lesson (GET one lesson) includes nested contents */
interface LessonDetail extends Lesson {
  contents: Content[];
}

interface Content {
  id: number;
  lesson: number; // FK lesson id
  title: string;
  content_type: LessonContentType;
  content: string; // body text or URL/embed; may be "" if only file
  file: string | null; // write: multipart file; read: often relative path or URL from storage
  file_url: string | null; // read-only absolute URL when a file exists
  order: number;
  created_at: string;
  updated_at: string;
}

/** Module with nested lessons (each lesson includes contents) */
interface ModuleDetail extends Module {
  lessons: LessonDetail[];
}

/** Full course tree (GET one course) */
interface CourseDetail extends Course {
  modules: ModuleDetail[];
}
```

### Content rules (mirror backend validation)

- **`content_type === "text"`**: `content` must be non-empty; do **not** send `file`.
- **`video` | `audio` | `document`**: at least one of `content` (trimmed non-empty) **or** `file` must be present (both allowed).

---

## Endpoint list

| Method | Path | Query params | Request body (JSON unless noted) | Success response |
|--------|------|----------------|-----------------------------------|------------------|
| GET | `/courses/` | `limit`, `offset`; with JWT: **`mine=1`** (instructor/admin only → my taught courses) | — **No auth** for public list | Paginated **`Course`** |
| POST | `/courses/` | — | JWT + `{ "title", "description", "slug?", "category?", "price?", "thumbnail?" (multipart), "instructor?": number }` | **Course** 201 |
| GET | `/courses/{id}/` | — | **No auth** → outline؛ با JWT و دسترسی کامل → **`CourseDetail`** | **`access_level`** + **`curriculum_requires_enrollment`**؛ **`GET …/curriculum/`** با JWT همان قفل enroll |
| GET | `/stats/` | — | — **No auth** | `{ "courses_count", "learners_count", "instructors_count" }` |
| POST | `/newsletter/` | — | `{ "email" }` **No auth** | `{ "email" }` 201 (duplicate email → 400) |
| PUT | `/courses/{id}/` | — | full **Course** fields you are allowed to change | **Course** |
| PATCH | `/courses/{id}/` | — | partial | **Course** |
| DELETE | `/courses/{id}/` | — | — | 204 |
| GET | `/modules/` | `course=<courseId>` optional | — | Paginated **Module** |
| POST | `/modules/` | — | `{ "course", "title", "description" }` | **Module** 201 |
| GET | `/modules/{id}/` | — | — | **Module** |
| PUT/PATCH/DELETE | `/modules/{id}/` | — | — | as usual |
| GET | `/lessons/` | `module=<moduleId>` optional | — | Paginated **Lesson** (list shape, no `contents`) |
| POST | `/lessons/` | — | `{ "module", "title", "content_type" }` | **Lesson** 201 |
| GET | `/lessons/{id}/` | — | — | **LessonDetail** (includes `contents`) |
| PUT/PATCH/DELETE | `/lessons/{id}/` | — | — | as usual |
| GET | `/contents/` | `lesson=<lessonId>` optional | — | Paginated **Content** |
| POST | `/contents/` | — | JSON or **`multipart/form-data`** if uploading `file` | **Content** 201 |
| GET | `/contents/{id}/` | — | — | **Content** |
| PUT/PATCH/DELETE | `/contents/{id}/` | — | multipart if updating `file` | **Content** |
| * | `/users/`, `/users/{id}/` | — | JWT **platform admin** only | DRF user CRUD |
| GET | `/admin/overview/` | — | JWT **platform admin** only | Site owner dashboard: `counts` + `recent` (users, enrollments, courses) |
| GET | `/messages/conversations/` | — | JWT | `{ "results": [ { "peer", "course", "last_message", "unread_count", "updated_at" } ] }` — inbox / messenger home |
| GET | `/messages/suggest-users/` | `q` (≥ 2 chars) | JWT | `{ "results": [UserBrief] }` — pick recipient |
| GET | `/messages/` | `peer`, `course`; `limit` / `offset` | JWT | Paginated **Message**; with **`peer`** = thread (default DM: no `course` param = `course` null only); **`?course=<id>`** without `peer` = all messages in that course |
| GET | `/messages/{id}/` | — | JWT | One **Message** (participant only) |
| POST | `/messages/` | — | `{ "recipient", "body", "course?": number }` | **Message** 201; recipient gets WebSocket `{ "type": "message", ... }` if connected |
| POST | `/messages/mark-read/` | — | `{ "peer": number, "course"?: number \| null }` | `{ "marked": <int> }`; notifies peer via WS `messages_read` |
| POST | `/messages/{id}/read/` | — | — | Marks read; WS `message_read` to sender |
| GET | `/notifications/` | `unread`, `limit` / `offset` | JWT | Paginated **Notification** (`kind`: message \| grade \| enrollment) |
| GET | `/notifications/unread-count/` | — | JWT | `{ "count": <int> }` |
| POST | `/notifications/{id}/read/` | — | — | Mark one read |
| POST | `/notifications/mark-all-read/` | — | — | `{ "marked": <int> }` |

New rows also pushed live on the **same WebSocket** as chat: `{ "type": "notification", "notification": { … } }`.

Router also exposes schema routes such as **`GET /api/v1/`** (API root listing).

**Django admin (`/admin/`)** is role-scoped: platform **`admin`** sees users + newsletter + full course data; **`instructor`** with **`is_staff`** sees only their own course tree in the courses app; students typically have no staff admin. See `docs/backend-api-contract-fa.md`.

---

## Example JSON

**POST /api/v1/courses/** (instructor)

```json
{
  "title": "Python 101",
  "description": "Intro course"
}
```

**POST /api/v1/courses/** (admin)

```json
{
  "title": "Python 101",
  "description": "Intro course",
  "instructor": 3
}
```

**POST /api/v1/contents/** (text lesson item)

```json
{
  "lesson": 12,
  "title": "Welcome",
  "content_type": "text",
  "content": "<p>Hello</p>",
  "order": 1
}
```

**POST /api/v1/contents/** (video with URL only)

```json
{
  "lesson": 12,
  "title": "Intro video",
  "content_type": "video",
  "content": "https://www.youtube.com/watch?v=...",
  "order": 2
}
```

---

## Typical frontend flows

1. **Course catalog**: `GET /api/v1/courses/?limit=20`
2. **Course player / syllabus**: `GET /api/v1/courses/{id}/` → render `modules[].lessons[].contents[]` sorted by `order`
3. **Edit one lesson’s blocks without loading full course**: `GET /api/v1/contents/?lesson=<lessonId>` (JWT + permission on that lesson’s course)
4. **Instructor dashboard**: same endpoints with JWT; mutations return 403 if not owner (and 401 if not logged in)
5. **Course player**: if **`access_level !== "full"`**, the API has no lesson bodies—re-fetch **`GET /courses/{id}/`** after login + enroll (or use **`GET …/curriculum/`** with JWT once enrolled).

---

## Error shape (DRF)

Validation: `{ "field_name": ["message"] }` or `{"detail": "..."}` / `non_field_errors`.

Status codes: **401** unauthenticated, **403** forbidden, **400** validation, **404** not found.
