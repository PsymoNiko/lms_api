# قرارداد API بک‌اند برای کلاینت LMS (Next.js)

این سند بر اساس کد فعلی مخزن کلاینت (`src/lib/api/*`, `src/lib/data/*`, ادمین و لندینگ) و پیاده‌سازی فعلی Django در این مخزن هم‌راستا شده است. پایهٔ مسیرها: **`/api/v1/`**.

---

## ۱) قراردادهای عمومی

| موضوع | انتظار کلاینت |
|--------|----------------|
| قالب JSON | پاسخ‌های خطا ترجیحاً DRF: `detail` (رشته)، `non_field_errors` (آرایه)، یا `{ "field": ["پیام"] }`. |
| صفحه‌بندی | `{ "count", "next", "previous", "results" }` — معمولاً `limit` و `offset` در query. |
| JWT | هدر **`Authorization: Bearer <access>`** برای درخواست‌های ادمین. |
| حذف موفق | **`204 No Content`** یا **`200`** با بدنهٔ خالی. |

---

## ۲) احراز هویت

### ۲.۱ ورود (توکن)

| متد | مسیر (پیش‌فرض) | احراز | بدنه (JSON) | پاسخ موفق (۲۰۰) | خطا |
|-----|------------------|--------|-------------|------------------|-----|
| `POST` | `/api/v1/login/` | بدون | `{ "username": "…", "password": "…" }` | `{ "access": "jwt", "refresh": "jwt" }` | ۴۰۱ / ۴۰۰ + `detail` یا فیلدها |

**تنظیم env:** اگر مسیر login فرق دارد → `NEXT_PUBLIC_API_TOKEN_URL` (مسیر کامل، یا نسبی با پروکسی).

### ۲.۲ تازه‌سازی access

| متد | مسیر | احراز | بدنه (JSON) | پاسخ موفق | خطا |
|-----|------|--------|-------------|------------|-----|
| `POST` | `/api/v1/refresh-token/` | بدون | `{ "refresh": "<refresh_jwt>" }` | حداقل `{ "access": "…" }`؛ اختیاری `{ "refresh": "…" }` برای چرخش refresh | ۴۰۱ / ۴۰۰ + `detail` |

کلاینت روی **۴۰۱** با توکن منقضی، یک بار refresh و تکرار درخواست را انجام می‌دهد. مسیرهای **`login/`** و **`refresh-token/`** از این حلقه معاف‌اند.

---

## ۳) API عمومی (بدون JWT)

### ۳.۱ لیست دوره‌ها

| متد | مسیر | Query | پاسخ ۲۰۰ | یادداشت |
|-----|------|---------|-----------|---------|
| `GET` | `/api/v1/courses/` | `limit`, `offset`؛ با JWT: **`mine=1`** (فقط **`instructor` / `admin`**) → فقط دوره‌هایی که کاربر **مدرس** آن است | `Paginated<Course>` | کاتالوگ عمومی؛ لندینگ `limit=6`. **بک‌اند: بدون JWT** برای لیست پیش‌فرض. |

**شکل هر `Course` در `results` (فیلدهایی که UI ممکن است بخواند):**

| فیلد | نوع تقریبی | الزام برای UI فعلی |
|------|-------------|---------------------|
| `id` | عدد | بله |
| `title`, `description` | رشته | بله |
| `instructor` | عدد | خیر |
| `instructor_detail` | شیء کاربر خلاصه | خیر؛ `email` اختیاری (برای ناشناس در Django حذف می‌شود) |
| `slug` | رشته | خیر |
| `thumbnail` / `thumbnail_url` | رشته / URL | خیر |
| `category` | رشته (می‌تواند خالی باشد) | خیر |
| `price` | عدد یا رشته (JSON معمولاً رشتهٔ Decimal) | خیر |
| `created_at`, `updated_at` | ISO string | خیر |

### ۳.۲ جزئیات دوره (درخت عمومی)

| متد | مسیر | پاسخ ۲۰۰ | ۴۰۴ |
|-----|------|-----------|-----|
| `GET` | `/api/v1/courses/{id}/` | بسته به دسترسی: **`access_level: "outline"`** (عمومی) یا **`"full"`** (ثبت‌نام / مدرس / ادمین) | ۴۰۴ دوره وجود ندارد |

**بک‌اند:** **بدون JWT** (یا کاربر بدون enroll) پاسخ شامل **`curriculum_requires_enrollment: true`** و outline است: `modules[].lessons[]` **بدون** آرایه **`contents`** و بدون متن/فایل درس. **درخت کامل** با **`contents`** و **`file_url`** وقتی **`access_level === "full"`** (کاربر enroll کرده یا مدرس همان دوره یا `admin`). **`GET …/curriculum/`** همچنان همان قفل را با JWT اعمال می‌کند.

**ساختار درخت کامل (`access_level: "full"` — همان `CourseDetail`):**

- `Course` + **`modules[]`**
  - هر ماژول: `id`, `course`, `title`, `description`, timestamps
  - **`lessons[]`**
    - هر درس: `id`, `module`, `title`, **`content_type`** ∈ `text` \| `video` \| `audio` \| `document`, timestamps
    - **`contents[]`**
      - `id`, `lesson`, `title`, **`content_type`**, **`content`** (رشته), **`file`**, **`file_url`**, `order`, timestamps

برای **پلیر ویدیو/صوت** در صفحهٔ دوره، **`file_url`** باید URL قابل پخش در `<video>` / `<audio>` باشد (معمولاً مطلق).

### ۳.۳ آمار لندینگ

| متد | مسیر | پاسخ ۲۰۰ (کلیدها ثابت) |
|-----|------|-------------------------|
| `GET` | `/api/v1/stats/` | `{ "courses_count", "learners_count", "instructors_count" }` |

### ۳.۴ خبرنامه

| متد | مسیر | بدنه | ۲۰۰/۲۰۱ | ۴۰۰ (مثال) |
|-----|------|------|-----------|-------------|
| `POST` | `/api/v1/newsletter/` | `{ "email": "…" }` | موفق | `{ "email": ["This address is already subscribed."] }` |

---

## ۴) API ادمین / مدرس (با JWT)

همهٔ مسیرهای زیر (به‌جز موارد عمومی بالا) با **`Authorization: Bearer`** فراخوانی می‌شوند. سطح دسترسی را بک‌اند تعیین می‌کند: **`student`** معمولاً فقط یادگیرنده است (بدون نوشتن روی `courses/` و بدون **`/users/`**)؛ **`instructor`** مالک دوره‌های خود؛ **`admin`** دسترسی گسترده + **`/users/`**. جزئیات: [`backend-api-contract-fa.md`](backend-api-contract-fa.md).

### ۴.۱ دوره‌ها `courses/`

| متد | مسیر | بدنه / Query | پاسخ ۲۰۰ |
|-----|------|--------------|-----------|
| `GET` | `courses/` | `limit`, `offset`؛ **`mine=1`** با JWT (مدرس/ادمین) | `Paginated<Course>` |
| `GET` | `courses/{id}/` | — | `CourseDetail` کامل یا نسخهٔ outline (فیلد **`access_level`**) |
| `POST` | `courses/` | JSON: `title`, `description`؛ اختیاری `instructor` (عدد) | شیء `Course` |
| `PATCH` | `courses/{id}/` | JSON جزئی: فعلاً UI ارسال می‌کند `title`, `description`, گاه `instructor` | شیء `Course` |
| `PUT` | `courses/{id}/` | پشتیبانی در کلاینت هست؛ فرم اصلی `PATCH` | شیء `Course` |
| `DELETE` | `courses/{id}/` | — | ۲۰۴ / بدنه خالی |

**تفاوت UI با مدل کامل بیزنس:** فیلدهایی مثل `slug`, `category`, `price`, آپلود `thumbnail` در فرم ادمین فعلی **ممکن است ارسال نشوند**؛ در Django اگر خالی باشند، **`slug`** از `title` پر می‌شود و **`price`** پیش‌فرض `0.00` است. برای کارت غنی‌تر، فرم ادمین را می‌توان گسترش داد.

### ۴.۲ ماژول‌ها `modules/`

| متد | مسیر | Query / بدنه | پاسخ |
|-----|------|----------------|------|
| `GET` | `modules/` | `course`, `limit`, `offset` | `Paginated<Module>` |
| `GET` | `modules/{id}/` | — | `Module` |
| `POST` | `modules/` | JSON: `course`, `title`, `description` | `Module` |
| `PATCH`/`PUT` | `modules/{id}/` | JSON جزئی/کامل | `Module` |
| `DELETE` | `modules/{id}/` | — | ۲۰۴ |

### ۴.۳ درس‌ها `lessons/`

| متد | مسیر | Query / بدنه | پاسخ |
|-----|------|----------------|------|
| `GET` | `lessons/` | `module`, `limit`, `offset` | `Paginated<Lesson>` |
| `GET` | `lessons/{id}/` | — | `Lesson` + `contents` (serializer جزئیات) |
| `POST` | `lessons/` | JSON: `module`, `title`, `content_type` | `Lesson` |
| `PATCH`/`PUT` | `lessons/{id}/` | JSON | `Lesson` |
| `DELETE` | `lessons/{id}/` | — | ۲۰۴ |

### ۴.۴ محتواها `contents/`

| متد | مسیر | بدنه | پاسخ |
|-----|------|------|------|
| `GET` | `contents/` | `lesson`, `limit`, `offset` | `Paginated<Content>` |
| `GET` | `contents/{id}/` | — | `Content` |
| `POST` | `contents/` | **الف)** JSON یا **ب)** `multipart/form-data` — جدول زیر | `Content` |
| `PATCH` | `contents/{id}/` | JSON یا `multipart` | `Content` |
| `DELETE` | `contents/{id}/` | — | ۲۰۴ |

**`POST` با JSON (`createContentJson`):**

```json
{
  "lesson": 1,
  "title": "…",
  "content_type": "text",
  "content": "…",
  "order": 0
}
```

**`POST` با `multipart` (`createContentMultipart`) — نام فیلدها دقیقاً این‌ها:**

| فیلد فرم | نوع | الزام در فرم ادمین |
|-----------|-----|---------------------|
| `lesson` | رشتهٔ عددی | بله |
| `title` | رشته | بله |
| `content_type` | یکی از `text`/`video`/`audio`/`document` | بله |
| `order` | رشتهٔ عددی | بله |
| `content` | رشته | اختیاری؛ برای `text` در UI اجباری منطقی است |
| `file` | فایل | اختیاری؛ برای آپلود مدیا/سند |

**`PATCH` با `multipart`:** همان الگو برای به‌روزرسانی فایل (`updateContentMultipart`).

### ۴.۵ ثبت‌نام در دوره، لیست enrollments، پیام، نمره (JWT)

| متد | مسیر | توضیح |
|-----|------|--------|
| POST | `/api/v1/auth/register/` | همان بدنهٔ **`/api/v1/register/`** (نام جایگزین برای فرانت). |
| POST | `/api/v1/courses/{id}/enroll/` | ثبت‌نام کاربر جاری در دوره؛ پاسخ شیء `Enrollment`. |
| GET | `/api/v1/enrollments/` | فقط enrollments کاربر لاگین؛ صفحه‌بندی DRF. |
| GET/POST | `/api/v1/messages/` | مسنجر: **`GET …/messages/conversations/`** inbox؛ **`GET …/messages/suggest-users/?q=`**؛ GET با **`?peer=`** (thread) و **`?course=`**؛ **`POST …/messages/mark-read/`** و **`POST …/messages/{id}/read/`**. POST بدنه `{ recipient, body, course? }`؛ پاسخ **`read`**, **`read_at`**, **`sender_detail`**, **`is_mine`**. |
| GET/POST | `/api/v1/notifications/`، **`…/unread-count/`**، **`…/mark-all-read/`**، **`…/{id}/read/`** | اعلان‌ها (`kind`: message, grade, enrollment)؛ سوکت **`type: notification`**. |
| GET | `/api/v1/admin/overview/` | **فقط ادمین پلتفرم**؛ شمارنده‌ها + `recent.users` / `recent.enrollments` / `recent.courses` برای داشبورد مالک سایت. |
| GET/PATCH | `/api/v1/grades/` و `/api/v1/grades/{id}/` | برای مدرس/ادمین فیلتر **`?course=`** روی GET؛ PATCH نمره (`score`, `feedback`, …). |
| * | `/api/v1/users/`، `/api/v1/users/{id}/` | **فقط ادمین پلتفرم** (`role=admin` یا superuser). |
| POST | `/api/v1/register/`، `/api/v1/auth/register/` | از API عمومی **نمی‌توان** نقش **`admin`** ساخت. |

---

## ۵) فراخوانی از سرور Next (SSR)

این درخواست‌ها از **Node** به آدرس **`INTERNAL_API_BASE_URL`** یا **`API_PROXY_TARGET`** می‌روند (بدون JWT):

| متد | مسیر | کاربرد |
|-----|------|--------|
| `GET` | `/api/v1/courses/?limit=6` | کارت‌های Featured |
| `GET` | `/api/v1/stats/` | نوار آمار |
| `GET` | `/api/v1/courses/{id}/` | برای SSR لندینگ: **outline** بدون JWT؛ برای صفحهٔ پلیر بعد از login + enroll از همان URL با **`access_level: "full"`** |

CORS برای این مسیر لازم نیست؛ باید از شبکهٔ سرور Next به Django دسترسی باشد.

---

## ۶) نقش کاربر در JSON (`UserBrief`)

کلاینت انتظار دارد در صورت وجود:

```json
{
  "id": 1,
  "username": "…",
  "role": "admin" | "instructor" | "student",
  "email": "…"
}
```

فیلد **`email`** در پاسخ‌های ناشناس **حذف می‌شود** (Django: `UserBriefSerializer`).

---

## ۷) چیزهایی که ممکن است در UI هنوز کامل وصل نشده باشد

- جستجوی هدر سایت  
- پرداخت / gateway  
- CRUD روی `slug` / `category` / `price` / `thumbnail` در فرم دورهٔ ادمین (API پشتیبانی می‌کند؛ UI در صورت نیاز گسترش یابد)

---

## ۸) مرجع کد تایپ‌ها در مخزن کلاینت

تعریف دقیق فیلدها در فرانت: **`src/lib/api/types.ts`** (مسیر مخزن Next).

---

# Server API checklist (synced with Django in this repo)

The Next app can call Django **from the browser** via **`NEXT_PUBLIC_API_USE_PROXY=true`** (same-origin `/api-backend/*` → rewrite in `next.config.ts`, no CORS).  
The **marketing homepage** fetches featured courses **on the server** using **`INTERNAL_API_BASE_URL`** (or `API_PROXY_TARGET`), so it does not need CORS.

## Already used by this client

| Area | Method | Path | Notes |
|------|--------|------|--------|
| Admin auth | POST | `/api/v1/login/` (or override `NEXT_PUBLIC_API_TOKEN_URL`) | Expect `{ access, refresh }` JSON |
| Register (alias) | POST | `/api/v1/auth/register/` | Same body/behavior as **`/api/v1/register/`** |
| Admin + catalog API | * | `/api/v1/courses/`, modules, lessons, contents | Bearer JWT for writes; modules/lessons/contents reads require JWT |
| Enroll + roster | POST/GET | `/api/v1/courses/{id}/enroll/`, `.../enrollments/` | JWT |
| My learning | GET | `/api/v1/enrollments/` | JWT; current user’s enrollments (paginated) |
| Messages / messenger | GET/POST | `/api/v1/messages/`, `…/conversations/`, `…/suggest-users/`, `…/mark-read/`, `…/{id}/read/` | JWT؛ thread با `peer` + اختیاری `course` |
| Grades | GET/PATCH | `/api/v1/grades/`, `/api/v1/grades/{id}/` | JWT; optional `?course=` for instructor/admin |
| Public (no JWT) | GET | `/api/v1/courses/`, `/api/v1/courses/{id}/` | `AllowAny`; **`{id}`** = outline until enrolled / staff (**`access_level`**) |
| Public | GET | `/api/v1/stats/` | Implemented |
| Public | POST | `/api/v1/newsletter/` | Implemented; throttled `30/hour` scope `newsletter` |

## Backend implementation status (this server)

| Priority item | Status |
|---------------|--------|
| 1. Public course list + optional card fields | **Done** — anonymous `GET /api/v1/courses/` and `GET /api/v1/courses/{id}/`; fields `slug`, `thumbnail`, `thumbnail_url`, `category`, `price` on `Course`. |
| 2. Public course detail for `/courses/[id]` | **Done** — outline for anonymous; full tree when `access_level: "full"` (enrolled / instructor / admin). |
| 3. CORS | **Only if browser hits Django directly** — `core/settings.py` allows `localhost:3000` and `127.0.0.1:3000`. |
| 4. Newsletter | **Done** — `POST /api/v1/newsletter/`. |
| 5. Stats | **Done** — `GET /api/v1/stats/`. |
| Testimonials API | **Not implemented** — still static/CMS if needed. |

## JWT contract

- Client expects JSON with **`access`** and **`refresh`** from the login/token endpoint (SimpleJWT).
- If your backend uses different keys or a cookie session only, adjust client `auth.ts` / storage.

## Env reference (client + server)

See **`.env.example`** in the Next repo for:

- `NEXT_PUBLIC_API_USE_PROXY` — browser → `/api-backend/*`
- `API_PROXY_TARGET` / `INTERNAL_API_BASE_URL` — Django base URL for rewrites + server fetch
- `NEXT_PUBLIC_API_BASE_URL` — direct API origin when **not** proxying

## Django reference (this repo)

| Topic | Location |
|-------|-----------|
| Course permissions (public GET) | `courses/views.py` — `CourseViewSet.get_permissions` |
| Serializers + public `email` strip | `courses/serializers.py` |
| Stats / newsletter | `courses/views.py`, `courses/urls.py` |
| Course catalog fields | `courses/models.py`, migration `0003_course_catalog_newsletter` |
| Short ops checklist | `docs/server-api-checklist.md` |
| Handoff (FA) | `docs/backend-handoff-fa.md`, `docs/backend-api-contract-fa.md` |
