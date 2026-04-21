# Server API checklist (for landing + full integration)

The Next app can call Django **from the browser** via **`NEXT_PUBLIC_API_USE_PROXY=true`** (same-origin `/api-backend/*` → rewrite in `next.config.ts`, no CORS).  
The **marketing homepage** fetches featured courses **on the server** using **`INTERNAL_API_BASE_URL`** (or `API_PROXY_TARGET`), so it does not need CORS.

**Full client ↔ server contract (Persian + English, field-level):** [`docs/lms-api-contract.md`](lms-api-contract.md)

---

## Already used by this client

| Area | Method | Path | Notes |
|------|--------|------|--------|
| Admin auth | POST | `/api/v1/login/` (or override `NEXT_PUBLIC_API_TOKEN_URL`) | Expect `{ access, refresh }` JSON |
| Admin + catalog API | * | `/api/v1/courses/`, modules, lessons, contents | Bearer JWT for writes; **modules / lessons / contents** list/detail still require JWT |
| Public (landing / SSR) | GET | `/api/v1/courses/`, `/api/v1/courses/{id}/` | **No JWT**؛ لیست کارت‌ها؛ **`{id}`** = metadata + syllabus outline فقط (`access_level: "outline"`، بدون محتوای درس). درخت کامل با **`access_level: "full"`** فقط بعد از enroll (یا مدرس/ادمین). |
| Public | GET | `/api/v1/stats/` | **No JWT** |
| Public | POST | `/api/v1/newsletter/` | **No JWT**; throttled `30/hour` (scope `newsletter`) |

---

## Recommended backend work (priority)

*(متن مرجع برای تیم محصول / فرانت؛ بدون قاطی شدن با وضعیت سرور.)*

### 1. Public course list (high) — unlocks landing “Featured” + future public catalog

- **Today:** `GET /api/v1/courses/` may require authentication. The homepage then falls back to placeholder cards.
- **Implement one of:**
  - **A)** Allow **anonymous GET** on list (and optionally detail) with a conservative serializer (no sensitive fields), **or**
  - **B)** Add **`GET /api/v1/public/courses/`** (and optional **`GET /api/v1/public/courses/{id}/`**) with `AllowAny`, pagination same as DRF (`limit` / `offset`).
- **Optional fields** on list for richer UI: `thumbnail` / `image_url`, `price`, `category`, `slug` for SEO links.

### 2. Align public course detail with app routes (medium)

- Public app has **`/courses/[courseId]`** (demo data today). For production, either:
  - Serve detail from **`GET /api/v1/courses/{id}/`** for everyone (read-only, nested tree), **or**
  - Add **`GET /api/v1/public/courses/{id}/`** with a reduced payload.

### 3. CORS (only if you do *not* use the Next proxy)

- If the browser calls `http://127.0.0.1:8000` directly, allow **`http://localhost:3000`** (and production origin) on **`Access-Control-Allow-Origin`**, methods, headers (`Authorization`, `Content-Type`), and credentials if you use cookies later.

### 4. Newsletter / lead capture (low, optional)

- **`POST /api/v1/newsletter/`** or similar: `{ "email": "..." }` for a footer form on the landing page (not built yet; say the word if you want it wired).

### 5. Stats / testimonials (low, optional)

- **`GET /api/v1/stats/`** — e.g. learners count, course count (for social proof section).
- **`GET /api/v1/testimonials/`** — curated quotes (or static JSON in CMS).

---

## Implemented on this Django server (summary)

| # | Topic | In this repo |
|---|--------|----------------|
| 1 | Public list + detail without JWT | **`GET /api/v1/courses/`**, **`GET /api/v1/courses/{id}/`** — `AllowAny`. جزئیات **`{id}`** برای ناشناس: **outline** (بدون `contents`). With JWT, **`?mine=1`** filters to courses the user **teaches** (`instructor` / `admin` only). Optional card fields: **`slug`**, **`thumbnail`**, **`thumbnail_url`**, **`category`**, **`price`** on `Course`. |
| 2 | Public course detail | **`GET /api/v1/courses/{id}/`** — anonymous / غیرمجاز: **outline** (بدون `contents`). enrolled یا staff: **`CourseDetail`** کامل. فیلدهای **`access_level`**, **`curriculum_requires_enrollment`**. |
| 3 | CORS for direct browser → Django | **`corsheaders`** + **`CORS_ALLOWED_ORIGINS`** (`localhost:3000`, `127.0.0.1:3000`) in `core/settings.py`. |
| 4 | Newsletter | **`POST /api/v1/newsletter/`** — `NewsletterSubscriber`, throttle `newsletter` **30/hour**. |
| 5a | Stats | **`GET /api/v1/stats/`** — `courses_count`, `learners_count`, `instructors_count`. |
| 5b | Testimonials | **Not implemented** — still optional / CMS. |
| 6 | Register alias | **`POST /api/v1/auth/register/`** → same **`RegisterView`** as **`/api/v1/register/`** (`accounts/urls.py`). |
| 7 | My enrollments | **`GET /api/v1/enrollments/`** — current user only (`MyEnrollmentViewSet`). |
| 8 | Messages + course | Optional **`course`** FK on **`Message`**; GET **`?course=`**; response field **`read`** (bool) plus **`read_at`**. |
| 9 | Grades by course | **`GET /api/v1/grades/?course=`** for admin/instructor. |
| 10 | Users API (admin) | **`/api/v1/users/`** — **`IsPlatformAdmin`** (`accounts/permissions.py`). |
| 11 | Django admin by role | **`core/admin_roles.py`**, **`courses/admin.py`**, **`accounts/admin.py`** — instructors scoped to own courses; newsletter/messages largely admin-only. |

**Anonymous course responses:** `instructor_detail.email` is omitted (`courses/serializers.py`).

---

## JWT contract

- Client expects JSON with **`access`** and **`refresh`** from the login/token endpoint (SimpleJWT).
- If your backend uses different keys or a cookie session only, say so and the client `auth.ts` / storage can be adjusted.

---

## Env reference (client + server)

See **`.env.example`** in the Next repo for:

- `NEXT_PUBLIC_API_USE_PROXY` — browser → `/api-backend/*`
- `API_PROXY_TARGET` / `INTERNAL_API_BASE_URL` — Django base URL for rewrites + server fetch
- `NEXT_PUBLIC_API_BASE_URL` — direct API origin when **not** proxying

---

## Django migrations (this server)

After pulling course catalog + newsletter changes:

```bash
python manage.py migrate courses
```
