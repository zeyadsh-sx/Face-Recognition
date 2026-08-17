# Face Recognition Attendance System

Automated student attendance using real-time facial recognition, with a desktop GUI and a live web dashboard.

> Year 2 Capstone Project

---

## Features

- Real-time face detection and recognition via OpenCV
- Anti-spoofing and mask detection
- Emotion detection during sessions
- Lecture session management (start → track → auto-mark absences on end)
- Live web dashboard with attendance stats and charts
- PDF report export and automated email notifications
- MySQL backend with a REST API (Flask)

---

## Project Structure

```
Face-Recognition/
├── core/          # Database, AI models, business logic
├── gui/           # Desktop app (Tkinter)
├── web/           # Web dashboard (Flask) + frontend assets
├── data/          # Face images and attendance snapshots
├── config/        # Email and settings config
├── run_gui.py     # Launch desktop app
└── setup_database_mysql.py
```

---

## Getting Started

**Requirements:** Python 3.10+, MySQL (e.g. XAMPP)

```bash
pip install -r requirements.txt
```

**1. Initialize the database (once)**
```bash
python setup_database_mysql.py
```

**2. Run the desktop app**
```bash
python run_gui.py
```

**3. Run the web dashboard**
```bash
python web/dashboard_final.py
```
Then open: http://localhost:5000

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/attendance/board?date=YYYY-MM-DD` | Attendance board for a date |
| POST | `/api/lecture/start` | Start a lecture session |
| POST | `/api/lecture/end` | End session and auto-mark absences |
| POST | `/api/attendance/manual` | Manually update attendance status |
| GET | `/api/attendance/report/pdf?date=YYYY-MM-DD` | Export PDF report |
| POST | `/api/email/report` | Send attendance report by email |

Full interactive docs available at `/apidocs` (Swagger).

---

## Configuration

- **Database:** Edit `mysql_config.py` (host, user, password, database)
- **Email:** Copy `.env.example` to `.env` and fill in SMTP credentials
- **Attendance settings** (late threshold, anti-spoofing): `core/attendance_settings.json`
