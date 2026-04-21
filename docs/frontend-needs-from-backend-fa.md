# آنچه فرانت از بک‌اند نیاز دارد (خلاصه + چت)

این فایل در **ریپو سرور** نگه داشته می‌شود تا تیم Next هم‌زمان با API جلو برود.

## چت‌روم (UI فعلی)

| نیاز | بک‌اند |
|------|--------|
| JWT با **`user_id`** در payload | SimpleJWT — `USER_ID_CLAIM = "user_id"` در `core/settings.py` |
| شکل پیام | `sender` / `recipient` عدد؛ `body`؛ `created_at`؛ اختیاری `course`؛ **`read`** (bool) |
| تاریخچه | `GET /api/v1/messages/?limit=200&offset=0` (DRF) |
| enroll + دوره | `GET /api/v1/enrollments/` و `GET /api/v1/courses/{id}/` برای عنوان و `instructor_detail` |
| **Real-time** | **`WebSocket`** — جزئیات: [`frontend-websocket-chat-fa.md`](frontend-websocket-chat-fa.md) |

### پیشنهادهای بعدی (P2+)

- `GET /api/v1/users/me/` برای پروفایل بدون پارس JWT دستی  
- resource جداگانهٔ `conversations` اگر بخواهید سرور threadها را خلاصه کند  
- **Redis channel layer** برای چند worker  
- **WebSocket** برای typing / read receipt (الان فقط send + deliver)

**لیست دانشجویان برای مدرس:**  
`GET /api/v1/courses/{id}/students/` — JWT، فقط مدرس/ادمین دوره.

---

## لینک مستقیم از `/learn` (پیشنهاد فرانت)

باز کردن `/messages?course=<id>&open=instructor` (یا peer id) — فقط UI؛ بک‌اند همان REST + WS بالا را دارد.
