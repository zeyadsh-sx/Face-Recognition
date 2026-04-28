from flask import Flask, Response, jsonify, request, send_file
try:
    from flasgger import Swagger
    FLASGGER_AVAILABLE = True
except ImportError:
    FLASGGER_AVAILABLE = False
import json
from datetime import datetime, date, timedelta
import os
from database_core_mysql import MySQLAttendanceDatabase
from services.export_service import ExportService

app = Flask(__name__, static_folder='frontend', static_url_path='/frontend')
app.secret_key = 'your-secret-key-here'

# إعداد واجهة Swagger لتوثيق الـ APIs
if FLASGGER_AVAILABLE:
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Smart Attendance API 🤖",
            "description": "Interactive Web Documentation for the Face Recognition Backend API.",
            "version": "1.0.0"
        }
    }
    Swagger(app, template=swagger_template)

# Initialize MySQL database
try:
    db = MySQLAttendanceDatabase()
    print("✅ MySQL Dashboard connected successfully!")
except Exception as e:
    print(f"❌ MySQL Dashboard connection failed: {e}")
    db = None

export_service = ExportService()

@app.route('/')
def dashboard():
    """Main dashboard without any template engine"""
    try:
        # Get today's statistics from MySQL
        today = date.today().isoformat()
        
        if db:
            attendance_records = db.get_attendance_with_emotions(today)
            students = db.get_all_students()
            
            total_students = len(students)
            present_students = len(attendance_records)
            absent_students = total_students - present_students
            attendance_rate = (present_students / total_students * 100) if total_students > 0 else 0
            
            # Emotion summary
            emotion_counts = {}
            for record in attendance_records:
                emotion = record.get('emotion', 'neutral')
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Get active alerts count
            alerts = db.get_active_alerts()
            active_alerts = len(alerts)
            
            stats = {
                'total_students': total_students,
                'present_students': present_students,
                'absent_students': absent_students,
                'attendance_rate': round(attendance_rate, 1),
                'emotion_summary': emotion_counts,
                'active_alerts': active_alerts,
                'date': today
            }
        else:
            stats = {
                'total_students': 0,
                'present_students': 0,
                'absent_students': 0,
                'attendance_rate': 0,
                'emotion_summary': {},
                'active_alerts': 0,
                'date': 'N/A'
            }
            attendance_records = []
        
        # Generate HTML directly (no template engine)
        html_content = generate_dashboard_html(stats, attendance_records)
        
        return Response(html_content, content_type='text/html; charset=utf-8')
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        error_html = generate_error_html(str(e))
        return Response(error_html, content_type='text/html; charset=utf-8')
# The real generate_dashboard_html() function is defined below.
def generate_dashboard_html(stats, attendance_records):
    
    emotion_html = ""
    if stats['emotion_summary']:
        for emotion, count in stats['emotion_summary'].items():
            emotion_html += f"""
            <div class="d-flex justify-content-between mb-2">
                <span>{emotion.capitalize()}</span>
                <span class="badge bg-primary">{count}</span>
            </div>
            """
    else:
        emotion_html = '<p class="text-muted">No emotion data available</p>'

    attendance_html = ""
    if attendance_records:
        for record in attendance_records:
            emotion_badge = f'<span class="badge bg-info">{record["emotion"]}</span>' if record.get('emotion') else 'N/A'
            real_face_icon = '✅' if record.get('is_real_face') else '❌'

            attendance_html += f"""
            <tr>
                <td>{record['name']}</td>
                <td>{record['time']}</td>
                <td>{emotion_badge}</td>
                <td>{real_face_icon}</td>
            </tr>
            """
    else:
        attendance_html = "<p>No attendance records for today</p>"

    return f"""
    <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition Attendance</title>
    <link rel="shortcut icon" href="/frontend/immigration.png" type="image/x-icon">
    <link rel="stylesheet" href="/frontend/bootstrap.min.css">
    <link rel="stylesheet" href="/frontend/style.css">
</head>

<body class="min-vh-100">
    <!-- //// header start -->
    <header class="position-sticky z-3 top-0 border-bottom ">
        <nav class="navbar mx-auto py-3 p-0">
            <div class="container">
                <a class="d-flex align-items-center gap-2 fs-4 fw-bold lh-sm text-danger text-decoration-none"
                    href="#home">
                    <span class="d-flex justify-content-center align-items-center rounded-12 nav-logo">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="20px" height="20px"
                            fill="#fff">
                            <path
                                d="M0 256a256 256 0 1 1 512 0 256 256 0 1 1 -512 0zM288 96a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM256 416c35.3 0 64-28.7 64-64 0-16.2-6-31.1-16-42.3l69.5-138.9c5.9-11.9 1.1-26.3-10.7-32.2s-26.3-1.1-32.2 10.7L261.1 288.2c-1.7-.1-3.4-.2-5.1-.2-35.3 0-64 28.7-64 64s28.7 64 64 64zM176 144a32 32 0 1 0 -64 0 32 32 0 1 0 64 0zM96 288a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm352-32a32 32 0 1 0 -64 0 32 32 0 1 0 64 0z" />
                        </svg>
                    </span>
                    MySQL <span class="text-primary">Dashboard</span>
                </a>
            </div>
        </nav>
    </header>
    <!-- //// header end-->
    <!-- /* ////// main start ////// */ -->
    <main id="home" class="py-32 mx-auto">
        <!-- ///// top boxs start ///// -->
        <section class="mb-32">
            <div class="row g-3">
                <div class="col-12 col-md-6 col-lg-3">
                    <div
                        class="px-3 py-2 top-box bg-white rounded-4 border border-danger d-flex align-items-center gap-3">
                        <div class="top-box-svg d-flex justify-content-center blue-box align-items-center rounded-12">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" width="20px" height="20px"
                                fill="#fff">
                                <path
                                    d="M320 16a104 104 0 1 1 0 208 104 104 0 1 1 0-208zM96 88a72 72 0 1 1 0 144 72 72 0 1 1 0-144zM0 416c0-70.7 57.3-128 128-128 12.8 0 25.2 1.9 36.9 5.4-32.9 36.8-52.9 85.4-52.9 138.6l0 16c0 11.4 2.4 22.2 6.7 32L32 480c-17.7 0-32-14.3-32-32l0-32zm521.3 64c4.3-9.8 6.7-20.6 6.7-32l0-16c0-53.2-20-101.8-52.9-138.6 11.7-3.5 24.1-5.4 36.9-5.4 70.7 0 128 57.3 128 128l0 32c0 17.7-14.3 32-32 32l-86.7 0zM472 160a72 72 0 1 1 144 0 72 72 0 1 1 -144 0zM160 432c0-88.4 71.6-160 160-160s160 71.6 160 160l0 16c0 17.7-14.3 32-32 32l-256 0c-17.7 0-32-14.3-32-32l0-16z" />
                            </svg>
                        </div>
                        <article>
                            <p class="mb-0 text-uppercase fw-semibold fs-12 text-light mt-2">total students</p>
                            <span class="fs-4 text-danger fw-bold">{stats['total_students']}</span>
                        </article>
                    </div>
                </div>
                <div class="col-12 col-md-6 col-lg-3">
                    <div
                        class="px-3 py-2 top-box bg-white rounded-4 border border-danger d-flex align-items-center gap-3">
                        <div class="top-box-svg d-flex justify-content-center orange-box align-items-center rounded-12">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" width="20px" height="20px"
                                fill="#fff">
                                <path
                                    d="M280 24a56 56 0 1 0 -112 0 56 56 0 1 0 112 0zm24 212.7L341 286.6c12.8-17.5 28.5-32.7 46.3-45l-56.2-75.7C306 132 266.3 112 224 112s-82 20-107.2 53.9l-70.5 95c-10.5 14.2-7.6 34.2 6.6 44.8s34.2 7.6 44.8-6.6L144 236.7 144 512c0 17.7 14.3 32 32 32s32-14.3 32-32l0-160c0-8.8 7.2-16 16-16s16 7.2 16 16l0 160c0 17.7 14.3 32 32 32s32-14.3 32-32l0-275.3zM640 400a144 144 0 1 0 -288 0 144 144 0 1 0 288 0zm-86.6-60.9c7.1 5.2 8.7 15.2 3.5 22.3l-64 88c-2.8 3.8-7 6.2-11.7 6.5s-9.3-1.3-12.6-4.6l-40-40c-6.2-6.2-6.2-16.4 0-22.6s16.4-6.2 22.6 0l26.8 26.8 53-72.9c5.2-7.1 15.2-8.7 22.4-3.5z" />
                            </svg>
                        </div>
                        <article>
                            <p class="mb-0 text-uppercase fw-semibold fs-12 text-light mt-2">present today</p>
                            <span class="fs-4 text-danger fw-bold">{stats['present_students']}</span>
                        </article>
                    </div>
                </div>
                <div class="col-12 col-md-6 col-lg-3">
                    <div
                        class="px-3 py-2 top-box bg-white rounded-4 border border-danger d-flex align-items-center gap-3">
                        <div class="top-box-svg d-flex justify-content-center red-box align-items-center rounded-12">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" width="20px" height="20px"
                                fill="#fff">
                                <path
                                    d="M280 24a56 56 0 1 0 -112 0 56 56 0 1 0 112 0zm24 212.7L341 286.6c12.8-17.5 28.5-32.7 46.3-45l-56.2-75.7C306 132 266.3 112 224 112s-82 20-107.2 53.9l-70.5 95c-10.5 14.2-7.6 34.2 6.6 44.8s34.2 7.6 44.8-6.6L144 236.7 144 512c0 17.7 14.3 32 32 32s32-14.3 32-32l0-160c0-8.8 7.2-16 16-16s16 7.2 16 16l0 160c0 17.7 14.3 32 32 32s32-14.3 32-32l0-275.3zM496 544a144 144 0 1 0 0-288 144 144 0 1 0 0 288zm22.6-144l36.7 36.7c6.2 6.2 6.2 16.4 0 22.6s-16.4 6.2-22.6 0l-36.7-36.7-36.7 36.7c-6.2 6.2-16.4 6.2-22.6 0s-6.2-16.4 0-22.6l36.7-36.7-36.7-36.7c-6.2-6.2-6.2-16.4 0-22.6s16.4-6.2 22.6 0l36.7 36.7 36.7-36.7c6.2-6.2 16.4-6.2 22.6 0s6.2 16.4 0 22.6L518.6 400z" />
                            </svg>
                        </div>
                        <article>
                            <p class="mb-0 text-uppercase fw-semibold fs-12 text-light mt-2">absent today</p>
                            <span class="fs-4 text-danger fw-bold">{stats['absent_students']}</span>
                        </article>
                    </div>
                </div>
                <div class="col-12 col-md-6 col-lg-3">
                    <div
                        class="px-3 py-2 top-box bg-white rounded-4 border border-danger d-flex align-items-center gap-3">
                        <div class="top-box-svg d-flex justify-content-center mix-box align-items-center rounded-12">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" width="20px" height="20px"
                                fill="#fff">
                                <path
                                    d="M192 128a96 96 0 1 0 -192 0 96 96 0 1 0 192 0zM448 384a96 96 0 1 0 -192 0 96 96 0 1 0 192 0zM438.6 86.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0l-384 384c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l384-384z" />
                            </svg>
                        </div>
                        <article>
                            <p class="mb-0 text-uppercase fw-semibold fs-12 text-light mt-2">attendance rate</p>
                            <span class="fs-4 text-danger fw-bold">{stats['attendance_rate']}%</span>
                        </article>
                    </div>
                </div>
            </div>
        </section>
        <!-- ///// top boxs end ///// -->
        <!-- /* ///mid boxs start /// */ -->
        <section class="mb-32">
            <div class="row g-3">
                <div class="col-12 col-md-6">
                    <div class="bg-white rounded-4 overflow-hidden border border-danger mid-boxs">
                        <div class="py-3 px-4 border-bottom-1 border-danger red-bg d-flex align-items-center gap-3">
                            <div class="red-box justify-content-center align-items-center d-flex rounded-3 mid-box-svg">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="#fff" width="18px"
                                    height="18px">
                                    <path
                                        d="M256 512a256 256 0 1 1 0-512 256 256 0 1 1 0 512zm0-192a32 32 0 1 0 0 64 32 32 0 1 0 0-64zm0-192c-18.2 0-32.7 15.5-31.4 33.7l7.4 104c.9 12.6 11.4 22.3 23.9 22.3 12.6 0 23-9.7 23.9-22.3l7.4-104c1.3-18.2-13.1-33.7-31.4-33.7z" />
                                </svg>
                            </div>
                            <article>
                                <h2 class="text-danger fw-bold fs-5 mt-1">Security Alerts</h2>
                            </article>
                        </div>
                        <div class="px-32 py-3 bg-white inner-box d-flex flex-column gap-3">
                            <div class="d-flex justify-content-between align-items-center border-bottom">
                                <div class="d-flex gap-2">
                                    <div
                                        class="outer-online rounded-2 d-flex justify-content-center align-items-center">
                                        <div class="rounded-circle bg-success inner-online"></div>
                                    </div>
                                    <p class="text-light fs-14">Active Alerts</p>
                                </div>
                                <span class="fs-6 fw-semibold text-danger mb-1">{stats['active_alerts']}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center border-bottom">
                                <div class="d-flex gap-2">
                                    <div
                                        class="outer-online rounded-2 d-flex justify-content-center align-items-center">
                                        <div class="rounded-circle bg-success inner-online"></div>
                                    </div>
                                    <p class="text-light fs-14">System Status</p>
                                </div>
                                <div class="bg-success bg-opacity-25 px-2 rounded-pill mb-3">
                                    <small class="text-success">connected</small>
                                </div>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <div class="d-flex gap-2">
                                    <div
                                        class="outer-online rounded-2 d-flex justify-content-center align-items-center">
                                        <div class="rounded-circle bg-success inner-online"></div>
                                    </div>
                                    <p class="text-light fs-14 mb-0">Last Updated</p>
                                </div>
                                <span class="fs-6 fw-semibold text-danger">{stats['date']}</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-12 col-md-6">
                    <div class="bg-white rounded-4 overflow-hidden border border-danger mid-boxs">
                        <div class="py-3 px-4 border-bottom-1 border-danger yellow-bg d-flex align-items-center gap-3">
                            <div
                                class="orange-box justify-content-center align-items-center d-flex rounded-3 mid-box-svg">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="#fff" width="18px"
                                    height="18px">
                                    <path
                                        d="M256 512a256 256 0 1 0 0-512 256 256 0 1 0 0 512zM386.7 308.9c11.9-3.7 23.9 6.3 19.6 18.1-22.4 61.3-81.3 105.1-150.3 105.1S128.1 388.2 105.7 326.9c-4.3-11.8 7.7-21.8 19.6-18.1 39.2 12.2 83.7 19.1 130.7 19.1s91.5-6.9 130.7-19.1zM328 196c-11 0-20 9-20 20s-9 20-20 20-20-9-20-20c0-33.1 26.9-60 60-60l16 0c33.1 0 60 26.9 60 60 0 11-9 20-20 20s-20-9-20-20-9-20-20-20l-16 0zM176 176a32 32 0 1 1 0 64 32 32 0 1 1 0-64z" />
                                </svg>
                            </div>
                            <article>
                                <h2 class="text-danger fw-bold fs-5 mt-1">Emotion Summary</h2>
                            </article>
                        </div>
                        <div class="px-32 py-3 bg-white d-flex justify-content-center align-items-center inner-box">
                            <p class="text-light fs-14 opacity-75">{emotion_html}</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <!-- /* ///mid boxs end /// */ -->
        <!-- /// last box start /// -->

        <section class="mb-32">
            <div class="bg-white rounded-4 overflow-hidden border border-danger mid-boxs">
                <div
                    class="py-3 px-4 border-bottom-1 border-danger blue-bg d-flex align-items-center gap-3 justify-content-between">
                    <div class="d-flex gap-2 align-items-center">
                        <div class="blue-box justify-content-center align-items-center d-flex rounded-3 mid-box-svg">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" fill="#fff" width="18px"
                                height="18px">
                                <path
                                    d="M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l192 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-192 0z" />
                            </svg>
                        </div>
                        <article>
                            <h2 class="text-danger fw-bold fs-5 mt-1 mb-1">Today's Attendance</h2>
                        </article>
                    </div>
                    <div>
                        <button type="button" class="btn btn-outline-primary d-flex align-items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="16px" height="16px"
                                fill="#0D6EFD">
                                <path
                                    d="M65.9 228.5c13.3-93 93.4-164.5 190.1-164.5 53 0 101 21.5 135.8 56.2 .2 .2 .4 .4 .6 .6l7.6 7.2-47.9 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l128 0c17.7 0 32-14.3 32-32l0-128c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 53.4-11.3-10.7C390.5 28.6 326.5 0 256 0 127 0 20.3 95.4 2.6 219.5 .1 237 12.2 253.2 29.7 255.7s33.7-9.7 36.2-27.1zm443.5 64c2.5-17.5-9.7-33.7-27.1-36.2s-33.7 9.7-36.2 27.1c-13.3 93-93.4 164.5-190.1 164.5-53 0-101-21.5-135.8-56.2-.2-.2-.4-.4-.6-.6l-7.6-7.2 47.9 0c17.7 0 32-14.3 32-32s-14.3-32-32-32L32 320c-8.5 0-16.7 3.4-22.7 9.5S-.1 343.7 0 352.3l1 127c.1 17.7 14.6 31.9 32.3 31.7S65.2 496.4 65 478.7l-.4-51.5 10.7 10.1c46.3 46.1 110.2 74.7 180.7 74.7 129 0 235.7-95.4 253.4-219.5z" />
                            </svg>
                            Refresh</button>
                    </div>
                </div>
                <div
                    class="px-32 py-3 bg-white d-flex justify-content-center align-items-center flex-column inner-box gap-3">
                    <div class="justify-content-center align-items-center d-flex rounded-circle last-box-svg">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" fill="#6a7282" width="26px"
                            height="26px">
                            <path
                                d="M128 0c17.7 0 32 14.3 32 32l0 32 128 0 0-32c0-17.7 14.3-32 32-32s32 14.3 32 32l0 32 32 0c35.3 0 64 28.7 64 64l0 288c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 128C0 92.7 28.7 64 64 64l32 0 0-32c0-17.7 14.3-32 32-32zm0 256c-17.7 0-32 14.3-32 32l0 64c0 17.7 14.3 32 32 32l192 0c17.7 0 32-14.3 32-32l0-64c0-17.7-14.3-32-32-32l-192 0z" />
                        </svg>
                    </div>
                    <article class="text-center">
                        <p class="mb-0 fw-bold text-danger">{attendance_html}</p>
                        <small class="text-light fs-12 opacity-75 fw-semibold">Data will appear here once students
                            submit their attendance</small>
                    </article>
                </div>
            </div>
        </section>
        <!-- /// last box end /// -->
    </main>
    <!-- /* ////// main end ////// */ -->
    <script src="/frontend/bootstrap.bundle.min.js"></script>
    <script>
        function downloadReport(event) {{
            event.preventDefault();
            const startDate = document.getElementById("start-date").value;
            const endDate = document.getElementById("end-date").value;
            const format = document.getElementById("export-format").value;
            if (!startDate || !endDate) {{
                alert("Please select both start and end dates.");
                return false;
            }}
            const url = `/api/reports/export?start=${{encodeURIComponent(startDate)}}&end=${{encodeURIComponent(endDate)}}&format=${{encodeURIComponent(format)}}`;
            window.open(url, '_blank');
            return false;
        }}
    </script>
    <script src="/frontend/index.js"></script>
</body>

</html>
    """
def generate_error_html(error_message):
    """Generate error page HTML"""
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Advanced Attendance System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .error-container {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
        }}
        .error-icon {{
            font-size: 80px;
            color: #dc3545;
            margin-bottom: 20px;
        }}
        .error-title {{
            color: #dc3545;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .error-message {{
            color: #6c757d;
            margin-bottom: 30px;
        }}
        .btn-primary {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">
            <i class="bi bi-exclamation-triangle-fill"></i>
        </div>
        <h1 class="error-title">حدث خطأ</h1>
        <div class="error-message">
            <p>{error_message}</p>
        </div>
        <div class="actions">
            <a href="/" class="btn btn-primary">
                <i class="bi bi-house"></i> العودة للرئيسية
            </a>
            <button onclick="history.back()" class="btn btn-outline-secondary ms-2">
                <i class="bi bi-arrow-right"></i> العودة للخلف
            </button>
        </div>
        <div class="mt-4">
            <small class="text-muted">
                <i class="bi bi-info-circle"></i> 
                إذا استمرت المشكلة، يرجى التحقق من:
                <ul class="text-start mt-2">
                    <li>تشغيل خادم MySQL</li>
                    <li>اتصال قاعدة البيانات</li>
                    <li>الملفات المطلوبة</li>
                </ul>
            </small>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """
    Get today's attendance summary
    ---
    tags:
      - Statistics API
    responses:
      200:
        description: Returns a daily summary including student counts and today's date.
        schema:
          type: object
          properties:
            total_students:
              type: integer
              description: Total registered students in the system.
            present_students:
              type: integer
              description: Number of students who attended today.
            date:
              type: string
              description: Today's date in YYYY-MM-DD format.
      500:
        description: System Database Failure.
        schema:
          type: object
          properties:
            error:
              type: string
    """
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        today = date.today().isoformat()
        attendance_records = db.get_attendance_with_emotions(today)
        students = db.get_all_students()
        
        return jsonify({
            'total_students': len(students),
            'present_students': len(attendance_records),
            'date': today
        })
    except Exception as e:
        return jsonify({'error': str(e)})
    

# ================== NEW API ENDPOINTS ==================

@app.route('/api/search', methods=['GET'])
def api_search():
    """Search for student by name"""
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        query = request.args.get('q', '').lower()
        students = db.get_all_students()
        
        results = [s for s in students if query in s['name'].lower()]
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/reports', methods=['GET'])
def api_reports():
    """Generate attendance report"""
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start and end dates required'})
        
        attendance = db.get_attendance_by_date_range(start_date, end_date)
        
        return jsonify({
            'period': f"{start_date} → {end_date}",
            'total_records': len(attendance),
            'data': attendance
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/reports/export', methods=['GET'])
def api_report_export():
    """Export attendance report in CSV, Excel, PDF or JSON."""
    if not db:
        return jsonify({'error': 'Database connection failed'})

    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        export_format = request.args.get('format', 'csv').lower()

        if not start_date or not end_date:
            return jsonify({'error': 'start and end dates required'})

        data = db.get_attendance_by_date_range(start_date, end_date)
        if data is None:
            return jsonify({'error': 'Could not retrieve attendance data'})

        export_dir = os.path.join(os.getcwd(), 'exports')
        os.makedirs(export_dir, exist_ok=True)
        base_name = f"attendance_{start_date}_{end_date}"

        if export_format == 'csv':
            filename = os.path.join(export_dir, f"{base_name}.csv")
            success, result = export_service.export_to_csv(data, filename)
        elif export_format == 'excel':
            filename = os.path.join(export_dir, f"{base_name}.xlsx")
            success, result = export_service.export_to_excel(data, filename)
        elif export_format == 'pdf':
            filename = os.path.join(export_dir, f"{base_name}.pdf")
            success, result = export_service.export_to_pdf(data, filename, title=f"Attendance Report {start_date} to {end_date}")
        elif export_format == 'json':
            filename = os.path.join(export_dir, f"{base_name}.json")
            success, result = export_service.export_to_json(data, filename)
        else:
            return jsonify({'error': 'Invalid export format'}), 400

        if not success:
            return jsonify({'error': result}), 500

        return send_file(result, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)})


# ================== FUTURE WORK ENDPOINTS ==================

@app.route('/api/charts', methods=['GET'])
def api_charts():
    """Charts data (Future Work)"""
    return jsonify({
        'status': 'coming_soon',
        'message': 'Charts API will provide visualization data'
    })


@app.route('/api/student', methods=['GET'])
def api_student():
    """Student details (Future Work)"""
    return jsonify({
        'status': 'coming_soon',
        'message': 'Student API will provide detailed student profile'
    })


@app.route('/api/live', methods=['GET'])
def api_live():
    """Live camera feed / detection (Future Work)"""
    return jsonify({
        'status': 'coming_soon',
        'message': 'Live API will stream real-time detection data'
    })


@app.route('/api/alerts', methods=['GET'])
def api_alerts():
    """System alerts (Future Work)"""
    return jsonify({
        'status': 'coming_soon',
        'message': 'Alerts API will manage system notifications'
    })


@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    """Advanced analytics (Future Work)"""
    return jsonify({
        'status': 'coming_soon',
        'message': 'Analytics API will provide deep insights'
    })

if __name__ == '__main__':
    print("🚀 Starting Final MySQL Dashboard...")
    print("📊 Connected to MySQL database")
    print("🌐 Dashboard will be available at: http://localhost:5000")
    print("📚 API Swagger Docs available at: http://localhost:5000/apidocs")
    print("=" * 50)
    print("📱 Mobile friendly - works on phones and tablets")
    print("🔄 Auto-refresh every 30 seconds")
    print("📈 Real-time analytics from MySQL database")
    print("=" * 50)
    print("🌐 Dashboard: http://localhost:5000")
    print("📚 Swagger UI: http://localhost:5000/apidocs")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    
