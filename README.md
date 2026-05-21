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
| طالب مسجّل مسبقاً | يُحفظ في `data/known_faces/<اسم_الطالب>/` + تسجيل حضور |
| شخص جديد يمر أمام الكاميرا | يُسجّل تلقائياً في `data/unknown_faces/temp_XXX/` (رقم مؤقت) بدون إضافته كطالب |
| تسجيل يدوي باسم | زر **Register Student** يحفظ في `known_faces/<الاسم>/` ويضيفه لقاعدة البيانات |

اضغط **q** في نافذة الكاميرا للإغلاق.

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
