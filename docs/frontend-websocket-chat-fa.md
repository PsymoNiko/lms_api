# WebSocket چت — قرارداد بک‌اند برای فرانت (Next.js)

## آدرس و احراز

| محیط | URL WebSocket |
|--------|----------------|
| لوکال (مستقیم به Django) | `ws://127.0.0.1:8000/ws/chat/?token=<ACCESS_JWT>` |
| HTTPS | `wss://<host>/ws/chat/?token=<ACCESS_JWT>` |
| از پشت پروکسی Next | اگر پروکسی فقط HTTP را فوروارد کند، **WebSocket را هم** به همان هاست Django (یا یک `NEXT_PUBLIC_WS_URL`) بدهید؛ `rewrites` معمولاً WS را تونل نمی‌کند مگر با پیکربندی جدا. |

**توکن:** همان **access** از `POST /api/v1/login/`؛ در query با نام **`token`** (نه `access`) تا با مرورگر سازگار باشد.

**JWT payload (SimpleJWT):** کلید **`user_id`** (عدد) در access token برای تراز حباب‌ها در فرانت کافی است — در `core/settings.py` با `USER_ID_CLAIM = "user_id"` ثابت شده است.

---

## رویدادها (JSON)

### بعد از اتصال موفق (سرور → کلاینت)

```json
{ "type": "connected", "user_id": 42 }
```

### ضربان (اختیاری)

**کلاینت → سرور:** `{ "type": "ping" }`  
**سرور → کلاینت:** `{ "type": "pong" }`

### در حال نوشتن (typing)

**کلاینت → سرور:**

```json
{ "type": "typing", "recipient": 3 }
```

**سرور → گیرنده (اگر آنلاین باشد):**

```json
{ "type": "typing", "from_user": 2 }
```

فقط اطلاع‌رسانی سبک؛ نرخ ارسال را در فرانت محدود کنید (مثلاً debounce).

### ارسال پیام (کلاینت → سرور)

```json
{
  "type": "send",
  "recipient": 3,
  "body": "متن پیام",
  "course": 12
}
```

- **`course`:** اختیاری؛ اگر نباشد یا `null` باشد، مثل REST ذخیره بدون دوره است.

### تحویل پیام (سرور → کلاینت)

هم به **فرستنده** (echo) و هم به **گیرنده** (اگر آنلاین باشد):

```json
{
  "type": "message",
  "message": {
    "id": 99,
    "sender": 2,
    "sender_detail": { "id": 2, "username": "...", "email": "...", "role": "instructor" },
    "recipient": 3,
    "course": 12,
    "body": "...",
    "read": false,
    "read_at": null,
    "is_mine": false,
    "created_at": "2026-04-21T12:00:00Z"
  }
}
```

شکل **`message`** همان **`MessageSerializer`** REST است (`read` بولین، `is_mine`، `sender_detail`).

### رویدادهای دیگر (سرور → کلاینت، بدون ذخیرهٔ جدا)

- **`POST /api/v1/messages/`** از طرف گیرنده با سوکت: `{ "type": "message", "message": { ... } }` (مثل بالا).
- **خوانده شدن دسته‌ای:** بعد از `POST /api/v1/messages/mark-read/` برای فرستندهٔ آن thread:

```json
{ "type": "messages_read", "reader_id": 3, "course": null, "count": 4 }
```

- **خوانده شدن یک پیام:** بعد از `POST /api/v1/messages/<id>/read/`:

```json
{ "type": "message_read", "message_id": 99, "reader_id": 3 }
```

### اعلان‌ها (notification)

همان اتصال سوکت؛ سرور برای کاربر مقصد:

```json
{
  "type": "notification",
  "notification": {
    "id": 1,
    "kind": "message",
    "title": "New message from …",
    "body": "…",
    "payload": { "message_id": 99, "sender_id": 2, "course_id": null },
    "read": false,
    "read_at": null,
    "created_at": "2026-04-21T12:00:00Z"
  }
}
```

انواع **`kind`:** `message` | `grade` | `enrollment`.  
REST: **`GET /api/v1/notifications/`**، **`GET /api/v1/notifications/unread-count/`**، **`POST …/notifications/<id>/read/`**، **`POST …/notifications/mark-all-read/`**.

### خطا

```json
{ "type": "error", "detail": "..." }
```

---

## هم‌زمانی با REST (مسنجر)

- **`GET /api/v1/messages/conversations/`** — لیست مکالمات: آخرین پیام، پیش‌نمایش، `unread_count`، `peer`، `course` (در صورت وجود).
- **`GET /api/v1/messages/suggest-users/?q=ab`** — جستجوی کاربر برای شروع گفتگو (حداقل ۲ حرف).
- **`GET /api/v1/messages/?peer=<id>`** — تاریخچهٔ **DM** با آن کاربر (`course` خالی).
- **`GET /api/v1/messages/?peer=<id>&course=<courseId>`** — همان thread مرتبط با دوره.
- **`POST /api/v1/messages/mark-read/`** — بدنه: `{ "peer": 3 }` برای DM؛ یا `{ "peer": 3, "course": 12 }` برای thread دوره (`course: null` صریح = DM).
- **`POST /api/v1/messages/<id>/read/`** — علامت‌گذاری یک پیام (فقط گیرنده).
- **`POST /api/v1/messages/`** — ارسال؛ گیرندهٔ آنلاین همان payload سوکت `{ "type": "message", ... }` را هم می‌گیرد.
- **`GET /api/v1/messages/?limit=…&offset=…`** — بدون `peer`: فید همهٔ پیام‌های مرتبط با کاربر (صفحه‌بندی DRF).
- پیام‌های WebSocket در **همان جدول** `Message` ذخیره می‌شوند.

---

## کانال‌ها (Channel layer)

- **توسعه:** `InMemoryChannelLayer` (پیش‌فرض فعلی) — برای یک پروسه `runserver` کافی است.
- **پروداکشن / چند worker:** `channels_redis` + `RedisChannelLayer` در `CHANNEL_LAYERS` تنظیم شود وگرنه سوکت بین پروسه‌ها broadcast نمی‌شود.

---

## اندپوینت جدید: لیست دانشجویان دوره (مدرس)

برای «گفتگوی جدید» از سمت مدرس:

`GET /api/v1/courses/{id}/students/` — **JWT**؛ فقط **مدرس آن دوره** یا **ادمین**.

پاسخ: آرایهٔ `{ "user": { "id", "username", "email", "role" }, "enrolled_at": "..." }`.

---

## اجرای سرور

با **`channels` + `daphne`** در `INSTALLED_APPS`، دستور معمول:

```bash
python manage.py runserver
```

باید هم HTTP و هم WebSocket را سرو کند. اگر WS وصل نشد، مستقیم:

```bash
daphne -b 127.0.0.1 -p 8000 core.asgi:application
```

---

## چک‌لیست فرانت برای اتصال

1. بعد از login، **`access`** را نگه دارید.
2. `new WebSocket(wsUrl)` با **`token=`** در query.
3. روی `onmessage`، JSON پارس کنید؛ اگر `type === "message"`، state گفتگو را به‌روز کنید.
4. برای UI مسنجر: **`GET /messages/conversations/`** برای inbox؛ برای باز کردن thread: **`GET /messages/?peer=…`** (و در صورت نیاز **`&course=`**).
5. **Origin:** در پروداکشن `ALLOWED_HOSTS` و در صورت نیاز `AllowedHostsOriginValidator` را با دامنهٔ فرانت هماهیم کنید.
