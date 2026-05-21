# Smart Face Recognition Attendance System

نظام حضور وغياب للطلاب بالتعرف على الوجه، مع واجهة سطح مكتب (GUI) ولوحة تحكم ويب.

---

## هيكل المشروع

```
Face-Recognition/
├── core/                    # قاعدة البيانات، الذكاء الاصطناعي، مسارات الملفات
│   ├── database_core_mysql.py
│   ├── features_ai_advanced.py
│   ├── face_capture_manager.py
│   ├── mysql_config.py
│   └── paths.py
├── gui/                     # تطبيق الكاميرا (Tkinter)
│   ├── gui_simple_mysql.py  # الواجهة الرئيسية
│   ├── gui_basic_mysql.py
│   ├── settings_panel.py
│   └── screenshot_capture.py
├── web/                     # لوحة التحكم (Flask)
│   ├── dashboard_final.py
│   ├── launcher_dashboard_mysql.py
│   ├── frontend/
│   └── templates/
├── data/                    # صور الوجوه والحضور
│   ├── known_faces/         # طالب معروف → مجلد باسمه
│   ├── unknown_faces/       # وجه جديد → temp_001, temp_002, ...
│   └── attendance_images/
├── config/
│   └── system_settings.json
├── start_mysql_app.py       # تشغيل GUI
├── run_gui.py
├── run_dashboard.py         # تشغيل الويب
└── setup_database_mysql.py
```

---

## سلوك الكاميرا

| الحالة | ماذا يحدث |
|--------|-----------|
| طالب مسجّل مسبقاً | `known_faces/<الاسم>/` + حضور (أو **متأخر** بعد بدء المحاضرة) + انصراف عند تكرار الظهور |
| شخص جديد | `unknown_faces/temp_XXX/` — ثم **تحويل temp → طالب** من الواجهة |
| تسجيل يدوي | تسجيل عادي أو **تسجيل بيانات كاملة** (رقم جامعي، شعبة، سنة، مجموعة) |

اضغط **q** في نافذة الكاميرا للإغلاق.

## ميزات الحضور والغياب (v2)

- **جلسة محاضرة**: بدء → تسجيل الحاضرين → إنهاء → غياب تلقائي لمن لم يظهر
- **لوحة حية**: حاضر / متأخر / غائب / معذور
- **تعديل يدوي** للحالة (present, late, absent, excused)
- **جدول حصص** (`class_schedule`)
- **Anti-spoofing** عند التسجيل (رفض الصور الوهمية)
- **تقرير غياب** من الواجهة والويب

### واجهة GUI — أزرار إضافية

| الزر | الوظيفة |
|------|---------|
| بدء/إنهاء محاضرة | جلسة + غياب آلي |
| لوحة حية | متابعة لحظية |
| تحويل temp → طالب | ربط مجهول باسم حقيقي |
| تعديل يدوي | تصحيح حضور/غياب |
| جدول الحصص | إضافة مواعيد |
| تقرير غياب | قائمة الغائبين والمتأخرين |

### API الويب (بعد تشغيل الداشبورد)

- `GET /api/attendance/board?date=YYYY-MM-DD`
- `GET /api/attendance/report?date=YYYY-MM-DD`
- `POST /api/lecture/start` — JSON: `name`, `course_code`, `section`, `late_threshold_minutes`
- `POST /api/lecture/end`
- `POST /api/attendance/manual` — `student_id`, `status`, `reason`
- `GET/POST /api/schedule`
- `GET /api/students?section=...`

إعدادات التأخير والكمامة: `core/attendance_settings.json`

---

## التشغيل

### 1) قاعدة البيانات (مرة واحدة)
```bash
python setup_database_mysql.py
```

### 2) واجهة الكاميرا (GUI)
```bash
python start_mysql_app.py
```
أو: `python run_gui.py`

### 3) لوحة التحكم (ويب)
```bash
python run_dashboard.py
```
ثم افتح: http://127.0.0.1:5000

---

## المتطلبات

- Python 3.10 أو 3.11 (مُوصى به لـ `face_recognition`)
- MySQL (مثل XAMPP)
- `pip install -r requirements.txt`

---

## ملاحظات

- الملفات القديمة في جذر المشروع (`database_core_mysql.py`, …) مجرد جسور توافق — استخدم مجلدات `core/` و `gui/` و `web/`.
- إعدادات MySQL في `core/mysql_config.py`.
