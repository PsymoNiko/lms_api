# قرارداد API (فشرده) — سرور Django

همه مسیرها با پیشوند **`/api/v1/`**.

## عمومی (بدون JWT)

| متد | مسیر |
|-----|------|
| GET | `/courses/` |
| GET | `/courses/{id}/` — **outline** (بدون `contents` / فایل درس) مگر با JWT + enroll یا مدرس/ادمین |
| GET | `/stats/` |
| POST | `/newsletter/` |

## احراز (بدون JWT روی خود endpoint)

| متد | مسیر |
|-----|------|
| POST | `/login/` |
| POST | `/register/` |
| POST | `/auth/register/` |
| POST | `/refresh-token/` |

## WebSocket (با JWT در query)

| | مسیر |
|--|------|
| WS | `/ws/chat/?token=<access_jwt>` |

جزئیات پیام JSON: [`frontend-websocket-chat-fa.md`](frontend-websocket-chat-fa.md).

## با JWT

| متد | مسیر | توضیح کوتاه |
|-----|------|--------------|
| GET | `/courses/?mine=1` | فقط **`admin` / `instructor`**؛ لیست دوره‌هایی که کاربر **مدرس** آن است |
| GET | `/courses/{id}/students/` | لیست دانشجویان ثبت‌نام‌شده (**مدرس همان دوره** یا **`admin`**) |
| POST | `/courses/{id}/enroll/` | ثبت‌نام؛ نقش **`student` / `instructor` / `admin`**؛ نه برای مدرس همان دوره |
| GET | `/courses/{id}/curriculum/` | درخت کامل؛ فقط در صورت **enroll** یا **مدرس/ادمین** |
| GET | `/courses/{id}/enrollments/` | روستر؛ فقط **مدرس همان دوره** یا **`admin`** |
| GET | `/enrollments/` | enrollments کاربر جاری |
| GET, POST | `/messages/` | مکالمه‌های مرتبط با کاربر؛ `?course=` اختیاری |
| GET | `/notifications/`، `/notifications/unread-count/` | اعلان‌های کاربر؛ **`?unread=1`** فقط نخوانده؛ زنده روی همان WebSocket چت با **`type: notification`** |
| POST | `/notifications/<id>/read/`، `/notifications/mark-all-read/` | خوانده‌شدن |
| GET, PATCH | `/grades/`, `/grades/{id}/` | **`admin`**: همه؛ **مدرس**: نمره‌های دوره‌های خود؛ **دانشجو**: فقط نمرهٔ خود؛ `?course=` برای مدرس/ادمین |
| * | `/modules/`, `/lessons/`, `/contents/` | **خواندن**: **`admin`** همه؛ **مدرس** دوره‌های خود (+ enroll شده)؛ **دانشجو** فقط دوره‌های enroll؛ **نوشتن**: **`admin`** یا **مدرس همان دوره** (نه دانشجو) |
| * | `/users/…` | **CRUD کاربران** فقط **`admin`** یا Django **superuser** (JWT) |
| GET | `/admin/overview/` | **فقط مالک سایت** (`admin` / superuser): آمار تجمیعی + لیست‌های اخیر برای پنل ادمین فرانت؛ در **`GET /me/`** فلگ **`access.can_access_site_owner_panel`** |

### نقش‌ها در یک نگاه (API)

- **`student`**: بدون JWT کاتالوگ و جزئیات عمومی؛ با JWT **enroll**، **enrollments**، **messages**، **notifications**، **grades** (خود)، **modules/lessons/contents** فقط برای دوره‌های enroll؛ **بدون** ایجاد/ویرایش/حذف دوره و بدون **users**.
- **`instructor`**: همان دانشجو برای یادگیری؛ علاوه بر آن **CRUD** روی دوره‌هایی که **`instructor`** آن است و محتوای وابسته؛ **`?mine=1`**؛ **students / enrollments** برای دورهٔ خود؛ **grades** برای شاگردان دورهٔ خود.
- **`admin`**: دسترسی کامل به دوره‌ها و نمره‌ها؛ **users**؛ روستر همهٔ دوره‌ها.

**ثبت‌نام عمومی** (`/register/`، `/auth/register/`): نقش **`admin`** قابل انتخاب نیست؛ **`admin`** فقط از پنل Django یا API **`/users/`** توسط ادمین.

## پنل Django (`/admin/`)

ورود به ادمین نیاز به **`is_staff=True`** دارد (تنظیم دستی توسط ادمین پلتفرم).

| نقش | ماژول‌های قابل مشاهده / رفتار |
|-----|------------------------------|
| **`admin`** (یا superuser) | کاربران (`CustomUser`)، پروفایل همه، **Newsletter**، **Notification**، **Message** (فقط خواندن/تغییر توسط ادمین)، درخت کامل دوره‌ها، enrollments، grades |
| **`instructor`** + staff | فقط اپ **courses**: دوره/ماژول/درس/محتوا/ثبت‌نام/نمره مربوط به **دوره‌های خود**؛ **Enrollment** بدون add (ثبت‌نام از API)؛ **Message** فقط رکوردهای مرتبط (محدود)؛ **Newsletter** نه |
| **`student`** | معمولاً **بدون** staff → بدون پنل courses؛ اگر staff باشد، queryset courses خالی است |

## خطا و صفحه‌بندی

DRF: `detail` / `non_field_errors` / فیلدها.  
صفحه‌بندی: `count`, `next`, `previous`, `results`.
