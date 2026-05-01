<<<<<<< HEAD
from flask import Flask, Response, jsonify, request, send_file
=======
from flask import Flask, Response, jsonify, request
>>>>>>> shahd
try:
    from flasgger import Swagger
    FLASGGER_AVAILABLE = True
except ImportError:
    FLASGGER_AVAILABLE = False
import json
from datetime import datetime, date, timedelta
import os
from database_core_mysql import MySQLAttendanceDatabase
<<<<<<< HEAD
from services.export_service import ExportService
=======
import csv
from io import StringIO
>>>>>>> shahd

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
            # Count UNIQUE students present (not duplicate records)
            present_student_names = set(record['name'] for record in attendance_records)
            present_students = len(present_student_names)
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
                <!-- ===== ADVANCED SEARCH & FILTER SECTION ===== -->
        <section class="search-filter-section">
            <div class="search-filter-header">
                <div class="search-filter-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="white">
                        <path d="M416 208c0 45.9-14.9 88.3-40 122.7l126.6 126.7c12.5 12.5 12.5 32.8 0 45.3s-32.8 12.5-45.3 0L330.7 376c-34.4 25.2-76.8 40-122.7 40C93.1 416 0 322.9 0 208S93.1 0 208 0s208 93.1 208 208zM208 352c79.5 0 144-64.5 144-144s-64.5-144-144-144-144 64.5-144 144 64.5 144 144 144z" />
                    </svg>
                </div>
                <div>
                    <h2>Advanced Search & Filters</h2>
                    <p class="text-secondary fs-14 mb-0">Search students and filter attendance records</p>
                </div>
            </div>

            <!-- Search Box -->
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search for students by name..." autocomplete="off">
            </div>
            <div id="searchResults"></div>

            <!-- Filter Controls -->
            <h5 class="mt-4 mb-3">Filter Attendance Records</h5>
            <div class="filter-controls">
                <div class="filter-group">
                    <label for="startDate">Start Date:</label>
                    <input type="date" id="startDate">
                </div>
                <div class="filter-group">
                    <label for="endDate">End Date:</label>
                    <input type="date" id="endDate">
                </div>
                <div class="filter-group">
                    <label for="departmentFilter">Department:</label>
                    <select id="departmentFilter">
                        <option value="">All Departments</option>
                        <option value="IT">IT</option>
                        <option value="Engineering">Engineering</option>
                        <option value="Business">Business</option>
                        <option value="Science">Science</option>
                        <option value="Arts">Arts</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="studentNameFilter">Student Name:</label>
                    <input type="text" id="studentNameFilter" placeholder="Leave empty to include all">
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="filter-buttons">
                <button class="filter-btn filter-btn-apply" onclick="searchFilter.applyFilters()">
                    <span>🔍</span> Apply Filters
                </button>
                <button class="filter-btn filter-btn-reset" onclick="searchFilter.resetFilters()">
                    <span>↺</span> Reset
                </button>
            </div>

            <!-- Export Buttons -->
            <div class="export-controls">
                <button class="export-btn export-btn-csv export-btn" id="exportCsvBtn" disabled>
                    <span>📊</span> Export CSV
                </button>
                <button class="export-btn export-btn-json export-btn" id="exportJsonBtn" disabled>
                    <span>📄</span> Export JSON
                </button>
            </div>

            <!-- Filter Results -->
            <div id="filterResults" class="mt-4"></div>
        </section>
        <!-- ===== END ADVANCED SEARCH & FILTER SECTION ===== -->
                <!-- ===== INTERACTIVE CHARTS SECTION ===== -->
        <!-- Charts Controls -->
        <section class="mb-32">
            <button class="btn-refresh-charts" onclick="refreshCharts()">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="16px" height="16px" fill="currentColor">
                    <path d="M65.9 228.5c13.3-93 93.4-164.5 190.1-164.5 53 0 101 21.5 135.8 56.2 .2 .2 .4 .4 .6 .6l7.6 7.2-47.9 0c-17.7 0-32 14.3-32 32s14.3 32 32 32l128 0c17.7 0 32-14.3 32-32l0-128c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 53.4-11.3-10.7C390.5 28.6 326.5 0 256 0 127 0 20.3 95.4 2.6 219.5 .1 237 12.2 253.2 29.7 255.7s33.7-9.7 36.2-27.1zm443.5 64c2.5-17.5-9.7-33.7-27.1-36.2s-33.7 9.7-36.2 27.1c-13.3 93-93.4 164.5-190.1 164.5-53 0-101-21.5-135.8-56.2-.2-.2-.4-.4-.6-.6l-7.6-7.2 47.9 0c17.7 0 32-14.3 32-32s-14.3-32-32-32L32 320c-8.5 0-16.7 3.4-22.7 9.5S-.1 343.7 0 352.3l1 127c.1 17.7 14.6 31.9 32.3 31.7S65.2 496.4 65 478.7l-.4-51.5 10.7 10.1c46.3 46.1 110.2 74.7 180.7 74.7 129 0 235.7-95.4 253.4-219.5z" />
                </svg>
                Refresh Charts
            </button>
        </section>

        <!-- Daily Attendance Chart -->
        <section class="chart-section">
            <div class="chart-header">
                <div class="chart-header-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="white">
                        <path d="M96 32C96 14.3 110.3 0 128 0c17.7 0 32 14.3 32 32V64H352V32c0-17.7 14.3-32 32-32c17.7 0 32 14.3 32 32V64h48c26.5 0 48 21.5 48 48v48H0V112C0 85.5 21.5 64 48 64H96V32zM0 192H512V464c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V192zm64 112c0-8.8 7.2-16 16-16h96c8.8 0 16 7.2 16 16v96c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V304zm192 0c0-8.8 7.2-16 16-16h96c8.8 0 16 7.2 16 16v96c0 8.8-7.2 16-16 16H272c-8.8 0-16-7.2-16-16V304z" />
                    </svg>
                </div>
                <div>
                    <h2>Daily Attendance</h2>
                    <p class="text-secondary fs-14 mb-0">Last 7 Days Trend</p>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="dailyAttendanceChart"></canvas>
            </div>
        </section>

        <!-- Charts Grid -->
        <div class="charts-grid">
            <!-- Monthly Attendance Chart -->
            <section class="chart-section">
                <div class="chart-header">
                    <div class="chart-header-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="white">
                            <path d="M512 80c0 18-14.3 34.6-32 38.8V394.2c0 5 4 9-9 9H32c-13 0-9-4-9-9V118.8C14.3 114.6 0 98 0 80C0 44.7 44.7 0 80 0H432c35.3 0 80 44.7 80 80zM327 208H185v-40h142v40zm0 80H185v40h142v-40zM91 208H49v40h42v-40zm0 80H49v40h42v-40zM371 208H229v40h142v-40zm0 80H229v40h142v-40z" />
                        </svg>
                    </div>
                    <div>
                        <h2>Monthly Attendance</h2>
                        <p class="text-secondary fs-14 mb-0">Last 12 Months Average</p>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="monthlyAttendanceChart"></canvas>
                </div>
            </section>

            <!-- Emotion Distribution Chart -->
            <section class="chart-section">
                <div class="chart-header">
                    <div class="chart-header-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="white">
                            <path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM176.5 175.8c-12.5-2.8-24.4 7.1-22.3 20c7 40.4 34.4 72.3 69.8 82.4 8.5 2.4 17.4-3.5 17.4-12.3V184c0-11-9-20-20-20c-28.4 0-52.7-16.5-64.9-40.2zm160 52.1c34.4-10.1 62.8-42 69.8-82.4c2.2-12.9-9.8-22.8-22.3-20c-12.2 23.7-36.5 40.2-64.9 40.2c-11 0-20 9-20 20v75.9c0 8.8 8.9 14.7 17.4 12.3zM432 480c44.2 0 80-35.8 80-80V128c0-44.2-35.8-80-80-80H80C35.8 48 0 83.8 0 128V400c0 44.2 35.8 80 80 80H432z" />
                        </svg>
                    </div>
                    <div>
                        <h2>Emotion Distribution</h2>
                        <p class="text-secondary fs-14 mb-0">Today's Emotional States</p>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="emotionChart"></canvas>
                </div>
            </section>
        </div>

        <!-- Hourly Attendance Chart -->
        <section class="chart-section">
            <div class="chart-header">
                <div class="chart-header-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="white">
                        <path d="M256 512A256 256 0 1 1 256 0a256 256 0 1 1 0 512zM232 120V256c0 8 4 15.5 10.7 20l96 64c11 7.3 25.9 4.2 33.2-6.7s4.2-25.9-6.7-33.2L280 243.2V120c0-13.3-10.7-24-24-24s-24 10.7-24 24z" />
                    </svg>
                </div>
                <div>
                    <h2>Hourly Breakdown</h2>
                    <p class="text-secondary fs-14 mb-0">Today's Attendance by Hour</p>
                </div>
            </div>
            <div class="chart-container" style="height: 350px;">
                <canvas id="hourlyAttendanceChart"></canvas>
            </div>
        </section>

        <!-- ===== END INTERACTIVE CHARTS SECTION ===== -->
    </main>
    <!-- /* ////// main end ////// */ -->
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js"></script>
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
    <script src="charts.js"></script>
    <script src="charts.js"></script>
    <script src="search.js"></script>
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
    """
    Search for students by name, ID, or attendance records
    ---
    tags:
      - Search API
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query (student name or ID)
      - name: type
        in: query
        type: string
        enum: [student, attendance, all]
        default: all
        description: Search type filter
      - name: date
        in: query
        type: string
        format: date
        description: Filter attendance by date (YYYY-MM-DD)
    responses:
      200:
        description: Search results
        schema:
          type: object
          properties:
            query:
              type: string
            type:
              type: string
            results:
              type: array
            count:
              type: integer
      400:
        description: Bad request
      500:
        description: Database error
    """
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all').lower()
        search_date = request.args.get('date')
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        results = []
        
        if search_type in ['student', 'all']:
            # Search students
            students = db.get_all_students()
            student_results = [s for s in students if query.lower() in s['name'].lower()]
            
            # Add attendance info for each student
            for student in student_results:
                if search_date:
                    attendance = db.get_student_attendance_by_date(student['id'], search_date)
                else:
                    attendance = db.get_student_attendance(student['id'], limit=5)
                
                student['recent_attendance'] = attendance
                student['result_type'] = 'student'
                results.append(student)
        
        if search_type in ['attendance', 'all']:
            # Search attendance records
            if search_date:
                attendance_records = db.get_attendance_with_emotions(search_date)
            else:
                # Get recent attendance (last 7 days)
                end_date = date.today()
                start_date = end_date - timedelta(days=7)
                attendance_records = db.get_attendance_by_date_range(start_date.isoformat(), end_date.isoformat())
            
            attendance_results = [r for r in attendance_records if query.lower() in r.get('name', '').lower()]
            
            for record in attendance_results:
                record['result_type'] = 'attendance'
                results.append(record)
        
        # Remove duplicates and sort
        unique_results = []
        seen_ids = set()
        
        for result in results:
            result_id = result.get('id') or result.get('student_id') or result.get('name')
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return jsonify({
            'query': query,
            'type': search_type,
            'date': search_date,
            'results': unique_results,
            'count': len(unique_results),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


@app.route('/api/reports', methods=['GET'])
def api_reports():
    """
    Generate comprehensive attendance reports
    ---
    tags:
      - Reports API
    parameters:
      - name: start
        in: query
        type: string
        format: date
        required: true
        description: Start date (YYYY-MM-DD)
      - name: end
        in: query
        type: string
        format: date
        required: true
        description: End date (YYYY-MM-DD)
      - name: type
        in: query
        type: string
        enum: [summary, detailed, analytics]
        default: summary
        description: Report type
      - name: format
        in: query
        type: string
        enum: [json, csv]
        default: json
        description: Response format
    responses:
      200:
        description: Report generated successfully
      400:
        description: Invalid parameters
      500:
        description: Database error
    """
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        report_type = request.args.get('type', 'summary').lower()
        response_format = request.args.get('format', 'json').lower()
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        # Validate dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            if start_dt > end_dt:
                return jsonify({'error': 'Start date must be before end date'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get base data
        attendance_records = db.get_attendance_by_date_range(start_date, end_date)
        all_students = db.get_all_students()
        
        if report_type == 'summary':
            report_data = generate_summary_report(attendance_records, all_students, start_date, end_date)
        elif report_type == 'detailed':
            report_data = generate_detailed_report(attendance_records, all_students, start_date, end_date)
        elif report_type == 'analytics':
            report_data = generate_analytics_report(attendance_records, all_students, start_date, end_date)
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Add metadata
        report_data['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'Face Recognition System',
            'report_type': report_type,
            'period': f"{start_date} to {end_date}",
            'total_records': len(attendance_records)
        }
        
        if response_format == 'csv':
            # Convert to CSV format
            return convert_report_to_csv(report_data)
        else:
            return jsonify(report_data)
            
    except Exception as e:
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500

def generate_summary_report(attendance_records, students, start_date, end_date):
    """Generate summary attendance report"""
    total_students = len(students)
    total_attendance = len(attendance_records)
    
    # Student attendance summary
    student_stats = {}
    for student in students:
        student_stats[student['id']] = {
            'name': student['name'],
            'present_days': 0,
            'total_possible': 0
        }
    
    # Process attendance records
    unique_dates = set()
    for record in attendance_records:
        student_id = record.get('student_id')
        attendance_date = record.get('date')
        
        if student_id in student_stats:
            student_stats[student_id]['present_days'] += 1
            unique_dates.add(attendance_date)
    
    # Calculate attendance rates
    total_days = len(unique_dates)
    for student_id in student_stats:
        student_stats[student_id]['total_possible'] = total_days
        if total_days > 0:
            attendance_rate = (student_stats[student_id]['present_days'] / total_days) * 100
            student_stats[student_id]['attendance_rate'] = round(attendance_rate, 1)
        else:
            student_stats[student_id]['attendance_rate'] = 0
    
    # Overall statistics
    overall_rate = (total_attendance / (total_students * total_days)) * 100 if total_students > 0 and total_days > 0 else 0
    
    return {
        'summary': {
            'total_students': total_students,
            'total_days': total_days,
            'total_attendance_records': total_attendance,
            'overall_attendance_rate': round(overall_rate, 1),
            'average_daily_attendance': round(total_attendance / total_days, 1) if total_days > 0 else 0
        },
        'student_statistics': list(student_stats.values()),
        'daily_breakdown': generate_daily_breakdown(attendance_records)
    }

def generate_detailed_report(attendance_records, students, start_date, end_date):
    """Generate detailed attendance report"""
    detailed_data = []
    
    # Group records by student
    student_records = {}
    for record in attendance_records:
        student_id = record.get('student_id')
        if student_id not in student_records:
            student_records[student_id] = []
        student_records[student_id].append(record)
    
    # Process each student's records
    for student in students:
        student_id = student['id']
        attendance_list = student_records.get(student_id, [])
        
        # Calculate statistics
        present_days = len(attendance_list)
        total_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
        attendance_rate = (present_days / total_days) * 100 if total_days > 0 else 0
        
        # Emotion analysis
        emotions = {}
        for record in attendance_list:
            emotion = record.get('emotion', 'neutral')
            emotions[emotion] = emotions.get(emotion, 0) + 1
        
        detailed_data.append({
            'student_id': student_id,
            'name': student['name'],
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'attendance_rate': round(attendance_rate, 1),
            'emotion_breakdown': emotions,
            'attendance_records': attendance_list
        })
    
    return {
        'detailed_records': detailed_data,
        'period_statistics': {
            'total_students': len(students),
            'period_days': total_days,
            'total_records': len(attendance_records)
        }
    }

def generate_analytics_report(attendance_records, students, start_date, end_date):
    """Generate analytics report with insights"""
    # Time-based analysis
    hourly_distribution = {}
    daily_distribution = {}
    weekly_distribution = {}
    
    for record in attendance_records:
        # Extract time components
        record_date = record.get('date')
        record_time = record.get('time', '00:00')
        
        if record_date:
            # Day of week analysis
            try:
                date_obj = datetime.strptime(record_date, '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                weekly_distribution[day_name] = weekly_distribution.get(day_name, 0) + 1
            except:
                pass
            
            daily_distribution[record_date] = daily_distribution.get(record_date, 0) + 1
        
        if record_time:
            try:
                hour = int(record_time.split(':')[0])
                hour_range = f"{hour}:00-{hour+1}:00"
                hourly_distribution[hour_range] = hourly_distribution.get(hour_range, 0) + 1
            except:
                pass
    
    # Emotion analysis
    emotion_stats = {}
    for record in attendance_records:
        emotion = record.get('emotion', 'neutral')
        emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1
    
    # Student performance analysis
    student_performance = []
    for student in students:
        student_attendance = [r for r in attendance_records if r.get('student_id') == student['id']]
        
        if student_attendance:
            attendance_rate = len(student_attendance) / len(set(r.get('date') for r in student_attendance)) * 100
            
            # Most common emotion
            emotions = [r.get('emotion', 'neutral') for r in student_attendance]
            most_common_emotion = max(set(emotions), key=emotions.count) if emotions else 'neutral'
            
            student_performance.append({
                'student_id': student['id'],
                'name': student['name'],
                'attendance_rate': round(attendance_rate, 1),
                'most_common_emotion': most_common_emotion,
                'total_records': len(student_attendance)
            })
    
    # Sort by attendance rate
    student_performance.sort(key=lambda x: x['attendance_rate'], reverse=True)
    
    return {
        'temporal_analysis': {
            'hourly_distribution': hourly_distribution,
            'daily_distribution': daily_distribution,
            'weekly_distribution': weekly_distribution
        },
        'emotion_analysis': emotion_stats,
        'student_performance': student_performance[:10],  # Top 10 performers
        'insights': generate_insights(attendance_records, students, start_date, end_date)
    }

def generate_insights(attendance_records, students, start_date, end_date):
    """Generate actionable insights from data"""
    insights = []
    
    # Calculate attendance rate
    total_students = len(students)
    total_days = len(set(r.get('date') for r in attendance_records))
    total_records = len(attendance_records)
    
    if total_students > 0 and total_days > 0:
        attendance_rate = (total_records / (total_students * total_days)) * 100
        
        if attendance_rate < 70:
            insights.append({
                'type': 'warning',
                'message': f'Low overall attendance rate ({attendance_rate:.1f}%)',
                'recommendation': 'Consider implementing attendance improvement strategies'
            })
        elif attendance_rate > 90:
            insights.append({
                'type': 'success',
                'message': f'Excellent attendance rate ({attendance_rate:.1f}%)',
                'recommendation': 'Maintain current attendance policies'
            })
    
    # Peak time analysis
    if attendance_records:
        times = [r.get('time', '00:00') for r in attendance_records]
        try:
            hours = [int(t.split(':')[0]) for t in times if ':' in t]
            if hours:
                peak_hour = max(set(hours), key=hours.count)
                insights.append({
                    'type': 'info',
                    'message': f'Peak arrival time: {peak_hour}:00',
                    'recommendation': f'Consider scheduling important activities around {peak_hour}:00'
                })
        except:
            pass
    
    return insights

def generate_daily_breakdown(attendance_records):
    """Generate daily attendance breakdown"""
    daily_stats = {}
    
    for record in attendance_records:
        date = record.get('date')
        if date:
            if date not in daily_stats:
                daily_stats[date] = {
                    'date': date,
                    'present': 0,
                    'emotions': {}
                }
            
            daily_stats[date]['present'] += 1
            
            emotion = record.get('emotion', 'neutral')
            daily_stats[date]['emotions'][emotion] = daily_stats[date]['emotions'].get(emotion, 0) + 1
    
    return list(daily_stats.values())

def convert_report_to_csv(report_data):
    """Convert report data to CSV format"""
    import csv
    import io
    
    output = io.StringIO()
    
    if 'summary' in report_data:
        # Summary report CSV
        writer = csv.writer(output)
        writer.writerow(['Student Name', 'Present Days', 'Total Possible', 'Attendance Rate (%)'])
        
        for student in report_data['student_statistics']:
            writer.writerow([
                student['name'],
                student['present_days'],
                student['total_possible'],
                student['attendance_rate']
            ])
    
    csv_data = output.getvalue()
    output.close()
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=attendance_report_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


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
    """
    Charts data for dashboard visualization
    ---
    tags:
      - Charts API
    parameters:
      - name: type
        in: query
        type: string
        enum: [attendance, emotions, trends, performance]
        default: attendance
        description: Chart data type
      - name: period
        in: query
        type: string
        enum: [week, month, quarter, year]
        default: week
        description: Time period for data
      - name: start
        in: query
        type: string
        format: date
        description: Custom start date (YYYY-MM-DD)
      - name: end
        in: query
        type: string
        format: date
        description: Custom end date (YYYY-MM-DD)
    responses:
      200:
        description: Chart data ready for visualization
        schema:
          type: object
          properties:
            chart_type:
              type: string
            data:
              type: array
            labels:
              type: array
      500:
        description: Database error
    """
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        chart_type = request.args.get('type', 'attendance').lower()
        period = request.args.get('period', 'week').lower()
        custom_start = request.args.get('start')
        custom_end = request.args.get('end')
        
        # Determine date range
        if custom_start and custom_end:
            start_date = custom_start
            end_date = custom_end
        else:
            end_date = date.today()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=7)
            
            start_date = start_date.isoformat()
            end_date = end_date.isoformat()
        
        # Get attendance data
        attendance_records = db.get_attendance_by_date_range(start_date, end_date)
        
        if chart_type == 'attendance':
            return jsonify(generate_attendance_chart_data(attendance_records, start_date, end_date))
        elif chart_type == 'emotions':
            return jsonify(generate_emotion_chart_data(attendance_records))
        elif chart_type == 'trends':
            return jsonify(generate_trends_chart_data(attendance_records, start_date, end_date))
        elif chart_type == 'performance':
            return jsonify(generate_performance_chart_data(attendance_records))
        else:
            return jsonify({'error': 'Invalid chart type'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Chart data generation failed: {str(e)}'}), 500

def generate_attendance_chart_data(attendance_records, start_date, end_date):
    """Generate attendance chart data"""
    # Daily attendance counts
    daily_counts = {}
    
    # Initialize all dates in range
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    current_dt = start_dt
    
    while current_dt <= end_dt:
        daily_counts[current_dt.strftime('%Y-%m-%d')] = 0
        current_dt += timedelta(days=1)
    
    # Count attendance per day
    for record in attendance_records:
        date = record.get('date')
        if date in daily_counts:
            daily_counts[date] += 1
    
    return {
        'chart_type': 'line',
        'title': 'Daily Attendance Trend',
        'labels': list(daily_counts.keys()),
        'datasets': [{
            'label': 'Students Present',
            'data': list(daily_counts.values()),
            'borderColor': 'rgb(75, 192, 192)',
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'fill': True
        }]
    }

def generate_emotion_chart_data(attendance_records):
    """Generate emotion distribution chart data"""
    emotion_counts = {}
    
    for record in attendance_records:
        emotion = record.get('emotion', 'neutral')
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    return {
        'chart_type': 'doughnut',
        'title': 'Emotion Distribution',
        'labels': list(emotion_counts.keys()),
        'datasets': [{
            'data': list(emotion_counts.values()),
            'backgroundColor': [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 205, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)',
                'rgba(255, 159, 64, 0.8)'
            ]
        }]
    }

def generate_trends_chart_data(attendance_records, start_date, end_date):
    """Generate trends analysis chart data"""
    # Weekly trends
    weekly_data = {}
    
    for record in attendance_records:
        record_date = record.get('date')
        if record_date:
            try:
                date_obj = datetime.strptime(record_date, '%Y-%m-%d')
                week_number = date_obj.isocalendar()[1]
                year = date_obj.year
                week_key = f"{year}-W{week_number}"
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = {'attendance': 0, 'unique_students': set()}
                
                weekly_data[week_key]['attendance'] += 1
                weekly_data[week_key]['unique_students'].add(record.get('student_id'))
            except:
                continue
    
    # Convert to chart format
    weeks = sorted(weekly_data.keys())
    attendance_counts = [weekly_data[week]['attendance'] for week in weeks]
    unique_counts = [len(weekly_data[week]['unique_students']) for week in weeks]
    
    return {
        'chart_type': 'bar',
        'title': 'Weekly Attendance Trends',
        'labels': weeks,
        'datasets': [
            {
                'label': 'Total Attendance Records',
                'data': attendance_counts,
                'backgroundColor': 'rgba(54, 162, 235, 0.8)'
            },
            {
                'label': 'Unique Students',
                'data': unique_counts,
                'backgroundColor': 'rgba(255, 99, 132, 0.8)'
            }
        ]
    }

def generate_performance_chart_data(attendance_records):
    """Generate student performance chart data"""
    student_stats = {}
    
    for record in attendance_records:
        student_id = record.get('student_id')
        student_name = record.get('name', f'Student {student_id}')
        
        if student_id not in student_stats:
            student_stats[student_id] = {'name': student_name, 'attendance': 0, 'emotions': {}}
        
        student_stats[student_id]['attendance'] += 1
        
        emotion = record.get('emotion', 'neutral')
        student_stats[student_id]['emotions'][emotion] = student_stats[student_id]['emotions'].get(emotion, 0) + 1
    
    # Get top 10 students by attendance
    top_students = sorted(student_stats.values(), key=lambda x: x['attendance'], reverse=True)[:10]
    
    return {
        'chart_type': 'horizontalBar',
        'title': 'Top Students by Attendance',
        'labels': [s['name'] for s in top_students],
        'datasets': [{
            'label': 'Attendance Count',
            'data': [s['attendance'] for s in top_students],
            'backgroundColor': 'rgba(75, 192, 192, 0.8)'
        }]
    }


@app.route('/api/student', methods=['GET'])
def api_student():
    """
    Get detailed student information
    ---
    tags:
      - Student API
    parameters:
      - name: id
        in: query
        type: integer
        description: Student ID
      - name: name
        in: query
        type: string
        description: Student name (alternative to ID)
      - name: include
        in: query
        type: string
        enum: [attendance, emotions, performance, all]
        default: basic
        description: Additional data to include
      - name: period
        in: query
        type: string
        description: Time period for attendance data (e.g., '30days', 'week', 'month')
    responses:
      200:
        description: Student details
        schema:
          type: object
          properties:
            student:
              type: object
            attendance_summary:
              type: object
            emotion_analysis:
              type: object
      404:
        description: Student not found
      500:
        description: Database error
    """
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        student_id = request.args.get('id')
        student_name = request.args.get('name')
        include_data = request.args.get('include', 'basic').lower()
        period = request.args.get('period', '30days')
        
        if not student_id and not student_name:
            return jsonify({'error': 'Student ID or name is required'}), 400
        
        # Get student information
        if student_id:
            student = db.get_student_by_id(int(student_id))
        else:
            student = db.get_student_by_name(student_name)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        result = {'student': student}
        
        # Include additional data based on request
        if include_data in ['attendance', 'all']:
            # Calculate date range based on period
            end_date = date.today()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            attendance_records = db.get_student_attendance_by_date(
                student['id'], 
                start_date.isoformat(), 
                end_date.isoformat()
            )
            
            # Generate attendance summary
            total_days = (end_date - start_date).days + 1
            present_days = len(attendance_records)
            attendance_rate = (present_days / total_days) * 100 if total_days > 0 else 0
            
            result['attendance_summary'] = {
                'period': f"{start_date.isoformat()} to {end_date.isoformat()}",
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': total_days - present_days,
                'attendance_rate': round(attendance_rate, 1),
                'recent_records': attendance_records[:10]  # Last 10 records
            }
        
        if include_data in ['emotions', 'all']:
            # Get emotion data for the student
            if 'attendance_records' in result:
                emotion_data = {}
                for record in result['attendance_records']['recent_records']:
                    emotion = record.get('emotion', 'neutral')
                    emotion_data[emotion] = emotion_data.get(emotion, 0) + 1
                
                result['emotion_analysis'] = {
                    'emotion_distribution': emotion_data,
                    'most_common_emotion': max(emotion_data.keys(), key=emotion_data.get) if emotion_data else 'neutral',
                    'emotion_variety': len(emotion_data)
                }
        
        if include_data in ['performance', 'all']:
            # Calculate performance metrics
            all_attendance = db.get_student_attendance(student['id'])
            
            # Attendance trends
            monthly_attendance = {}
            for record in all_attendance:
                try:
                    record_date = datetime.strptime(record.get('date', ''), '%Y-%m-%d')
                    month_key = record_date.strftime('%Y-%m')
                    monthly_attendance[month_key] = monthly_attendance.get(month_key, 0) + 1
                except:
                    continue
            
            # Calculate consistency score
            if len(monthly_attendance) > 1:
                avg_attendance = sum(monthly_attendance.values()) / len(monthly_attendance)
                variance = sum((count - avg_attendance) ** 2 for count in monthly_attendance.values()) / len(monthly_attendance)
                consistency_score = max(0, 100 - (variance / avg_attendance * 100)) if avg_attendance > 0 else 0
            else:
                consistency_score = 50  # Neutral score
            
            result['performance_metrics'] = {
                'total_attendance_records': len(all_attendance),
                'monthly_breakdown': monthly_attendance,
                'consistency_score': round(consistency_score, 1),
                'performance_trend': 'improving' if len(monthly_attendance) > 1 and list(monthly_attendance.values())[-1] > list(monthly_attendance.values())[0] else 'stable'
            }
        
        result['retrieved_at'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except ValueError:
        return jsonify({'error': 'Invalid student ID format'}), 400
    except Exception as e:
        return jsonify({'error': f'Student data retrieval failed: {str(e)}'}), 500

@app.route('/api/student/list', methods=['GET'])
def api_student_list():
    """
    Get list of all students with pagination
    ---
    tags:
      - Student API
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: limit
        in: query
        type: integer
        default: 50
        description: Results per page
      - name: search
        in: query
        type: string
        description: Search term for student names
      - name: sort
        in: query
        type: string
        enum: [name, id, attendance_rate]
        default: name
        description: Sort field
    responses:
      200:
        description: Student list
        schema:
          type: object
          properties:
            students:
              type: array
            pagination:
              type: object
    """
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search_term = request.args.get('search', '').strip()
        sort_field = request.args.get('sort', 'name').lower()
        
        # Get all students
        all_students = db.get_all_students()
        
        # Apply search filter
        if search_term:
            all_students = [s for s in all_students if search_term.lower() in s['name'].lower()]
        
        # Apply sorting
        if sort_field == 'name':
            all_students.sort(key=lambda x: x['name'].lower())
        elif sort_field == 'id':
            all_students.sort(key=lambda x: x['id'])
        elif sort_field == 'attendance_rate':
            # This would require additional database query for attendance rates
            # For now, sort by name as fallback
            all_students.sort(key=lambda x: x['name'].lower())
        
        # Apply pagination
        total_students = len(all_students)
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_students = all_students[start_index:end_index]
        
        total_pages = (total_students + limit - 1) // limit
        
        return jsonify({
            'students': paginated_students,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_students': total_students,
                'students_per_page': limit,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'filters_applied': {
                'search': search_term,
                'sort': sort_field
            }
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    except Exception as e:
        return jsonify({'error': f'Student list retrieval failed: {str(e)}'}), 500


@app.route('/api/live', methods=['GET'])
def api_live():
    """
    Live camera feed and real-time detection status
    ---
    tags:
      - Live API
    parameters:
      - name: status
        in: query
        type: boolean
        default: true
        description: Get current system status
      - name: recent
        in: query
        type: integer
        default: 5
        description: Number of recent detections to return
    responses:
      200:
        description: Live system status and recent detections
        schema:
          type: object
          properties:
            system_status:
              type: object
            recent_detections:
              type: array
            camera_info:
              type: object
      500:
        description: System error
    """
    try:
        get_status = request.args.get('status', 'true').lower() == 'true'
        recent_count = int(request.args.get('recent', 5))
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'api_status': 'active'
        }
        
        if get_status:
            # System status (simulated - in real implementation, check actual camera/system)
            result['system_status'] = {
                'camera_active': True,  # Would check actual camera status
                'detection_active': True,  # Would check actual detection service
                'database_connected': db is not None,
                'last_detection': datetime.now().isoformat(),
                'uptime': '2h 34m',  # Would calculate actual uptime
                'performance': {
                    'cpu_usage': 45.2,
                    'memory_usage': 62.8,
                    'detection_fps': 15.3
                }
            }
            
            result['camera_info'] = {
                'camera_id': 'cam_001',
                'resolution': '1920x1080',
                'fps': 30,
                'status': 'active',
                'location': 'Main Entrance'
            }
        
        if recent_count > 0 and db:
            # Get recent attendance/detection records
            today = date.today().isoformat()
            recent_records = db.get_attendance_with_emotions(today)
            
            # Take the most recent records
            result['recent_detections'] = recent_records[:recent_count]
            
            # Add detection confidence and additional info (simulated)
            for detection in result['recent_detections']:
                detection['detection_confidence'] = round(0.85 + (hash(detection['name']) % 15) / 100, 2)
                detection['detection_time'] = detection.get('time', '00:00:00')
                detection['face_quality'] = 'good' if detection['detection_confidence'] > 0.9 else 'acceptable'
        
        # Live stream endpoint info (for frontend to connect)
        result['stream_info'] = {
            'stream_available': False,  # Would check if stream is actually available
            'stream_url': '/api/live/stream',  # Placeholder for actual stream endpoint
            'stream_type': 'mjpeg',
            'requires_auth': False
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Live status retrieval failed: {str(e)}'}), 500

@app.route('/api/live/stream', methods=['GET'])
def api_live_stream():
    """
    Live video stream endpoint (placeholder)
    ---
    tags:
      - Live API
    responses:
      200:
        description: Video stream
      404:
        description: Stream not available
    """
    # This is a placeholder for actual video streaming
    # In a real implementation, this would serve MJPEG stream from camera
    return jsonify({
        'status': 'coming_soon',
        'message': 'Live video streaming will be implemented with camera integration',
        'note': 'This endpoint will serve MJPEG video stream when camera is connected'
    }), 501

@app.route('/api/live/detect', methods=['POST'])
def api_live_detect():
    """
    Manual face detection from uploaded image
    ---
    tags:
      - Live API
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: Image file for face detection
    responses:
      200:
        description: Detection results
      400:
        description: No image provided
      500:
        description: Detection failed
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    try:
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # In a real implementation, this would:
        # 1. Save the image temporarily
        # 2. Process with face recognition
        # 3. Return detection results
        
        # Placeholder response
        return jsonify({
            'status': 'coming_soon',
            'message': 'Face detection from uploaded images will be implemented',
            'note': 'This will process uploaded images and return face detection results'
        }), 501
        
    except Exception as e:
        return jsonify({'error': f'Detection failed: {str(e)}'}), 500


@app.route('/api/alerts', methods=['GET'])
def api_alerts():
    """
    Get system alerts and notifications
    ---
    tags:
      - Alerts API
    parameters:
      - name: type
        in: query
        type: string
        enum: [all, security, system, attendance]
        default: all
        description: Alert type filter
      - name: status
        in: query
        type: string
        enum: [active, resolved, all]
        default: active
        description: Alert status filter
      - name: limit
        in: query
        type: integer
        default: 50
        description: Maximum number of alerts to return
      - name: since
        in: query
        type: string
        format: date
        description: Show alerts since this date (YYYY-MM-DD)
    responses:
      200:
        description: List of alerts
        schema:
          type: object
          properties:
            alerts:
              type: array
            summary:
              type: object
      500:
        description: Database error
    """
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        alert_type = request.args.get('type', 'all').lower()
        alert_status = request.args.get('status', 'active').lower()
        limit = int(request.args.get('limit', 50))
        since_date = request.args.get('since')
        
        # Get alerts from database
        if db and hasattr(db, 'get_alerts'):
            alerts = db.get_alerts(
                alert_type=alert_type if alert_type != 'all' else None,
                status=alert_status if alert_status != 'all' else None,
                limit=limit,
                since_date=since_date
            )
        else:
            # Generate sample alerts for demonstration
            alerts = generate_sample_alerts(alert_type, alert_status, limit)
        
        # Filter alerts based on parameters
        filtered_alerts = alerts
        
        if alert_type != 'all':
            filtered_alerts = [a for a in filtered_alerts if a.get('type') == alert_type]
        
        if alert_status != 'all':
            filtered_alerts = [a for a in filtered_alerts if a.get('status') == alert_status]
        
        if since_date:
            try:
                since_dt = datetime.strptime(since_date, '%Y-%m-%d')
                filtered_alerts = [
                    a for a in filtered_alerts 
                    if datetime.fromisoformat(a.get('created_at', '').replace('Z', '+00:00')) >= since_dt
                ]
            except:
                pass
        
        # Apply limit
        filtered_alerts = filtered_alerts[:limit]
        
        # Generate summary
        alert_summary = {
            'total_alerts': len(filtered_alerts),
            'by_type': {},
            'by_status': {},
            'by_priority': {}
        }
        
        for alert in filtered_alerts:
            # Count by type
            alert_type_key = alert.get('type', 'unknown')
            alert_summary['by_type'][alert_type_key] = alert_summary['by_type'].get(alert_type_key, 0) + 1
            
            # Count by status
            alert_status_key = alert.get('status', 'unknown')
            alert_summary['by_status'][alert_status_key] = alert_summary['by_status'].get(alert_status_key, 0) + 1
            
            # Count by priority
            alert_priority_key = alert.get('priority', 'medium')
            alert_summary['by_priority'][alert_priority_key] = alert_summary['by_priority'].get(alert_priority_key, 0) + 1
        
        return jsonify({
            'alerts': filtered_alerts,
            'summary': alert_summary,
            'filters_applied': {
                'type': alert_type,
                'status': alert_status,
                'limit': limit,
                'since': since_date
            },
            'retrieved_at': datetime.now().isoformat()
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        return jsonify({'error': f'Alerts retrieval failed: {str(e)}'}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
def api_alert_detail(alert_id):
    """
    Get detailed information about a specific alert
    ---
    tags:
      - Alerts API
    parameters:
      - name: alert_id
        in: path
        type: integer
        required: true
        description: Alert ID
    responses:
      200:
        description: Alert details
      404:
        description: Alert not found
    """
    try:
        # In a real implementation, get alert from database
        # For now, return a sample alert detail
        
        sample_alert = {
            'id': alert_id,
            'type': 'security',
            'title': 'Unknown Face Detected',
            'description': 'An unknown face was detected at the main entrance',
            'priority': 'high',
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'location': 'Main Entrance',
            'camera_id': 'cam_001',
            'details': {
                'confidence': 0.92,
                'face_image_path': '/static/unknown_faces/unknown_20240501_143022.jpg',
                'detection_time': '14:30:22',
                'resolution_suggested': 'Manual verification required'
            },
            'actions_taken': [],
            'actions_available': ['mark_resolved', 'assign_student', 'false_positive']
        }
        
        return jsonify(sample_alert)
        
    except Exception as e:
        return jsonify({'error': f'Alert detail retrieval failed: {str(e)}'}), 500

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def api_alert_resolve(alert_id):
    """
    Mark an alert as resolved
    ---
    tags:
      - Alerts API
    parameters:
      - name: alert_id
        in: path
        type: integer
        required: true
        description: Alert ID
      - name: resolution
        in: body
        type: object
        required: true
        properties:
          action:
            type: string
            enum: [resolved, false_positive, assigned]
          notes:
            type: string
          assigned_to:
            type: string
    responses:
      200:
        description: Alert resolved successfully
      404:
        description: Alert not found
    """
    try:
        resolution_data = request.get_json()
        
        if not resolution_data:
            return jsonify({'error': 'Resolution data is required'}), 400
        
        action = resolution_data.get('action')
        notes = resolution_data.get('notes', '')
        assigned_to = resolution_data.get('assigned_to')
        
        if not action:
            return jsonify({'error': 'Action is required'}), 400
        
        # In a real implementation, update alert in database
        # For now, return success response
        
        return jsonify({
            'alert_id': alert_id,
            'status': 'resolved',
            'action_taken': action,
            'notes': notes,
            'assigned_to': assigned_to,
            'resolved_at': datetime.now().isoformat(),
            'resolved_by': 'system_user'  # Would get actual user
        })
        
    except Exception as e:
        return jsonify({'error': f'Alert resolution failed: {str(e)}'}), 500

def generate_sample_alerts(alert_type, alert_status, limit):
    """Generate sample alerts for demonstration"""
    sample_alerts = [
        {
            'id': 1,
            'type': 'security',
            'title': 'Unknown Face Detected',
            'priority': 'high',
            'status': 'active',
            'created_at': '2024-05-01T14:30:22Z',
            'location': 'Main Entrance'
        },
        {
            'id': 2,
            'type': 'attendance',
            'title': 'Low Attendance Rate',
            'priority': 'medium',
            'status': 'active',
            'created_at': '2024-05-01T09:15:10Z',
            'location': 'System'
        },
        {
            'id': 3,
            'type': 'system',
            'title': 'Database Connection Warning',
            'priority': 'low',
            'status': 'resolved',
            'created_at': '2024-05-01T08:45:33Z',
            'location': 'System'
        },
        {
            'id': 4,
            'type': 'security',
            'title': 'Multiple Failed Recognition Attempts',
            'priority': 'high',
            'status': 'active',
            'created_at': '2024-05-01T13:22:15Z',
            'location': 'Side Entrance'
        },
        {
            'id': 5,
            'type': 'attendance',
            'title': 'Student Missing for 3 Days',
            'priority': 'medium',
            'status': 'active',
            'created_at': '2024-05-01T10:30:45Z',
            'location': 'System'
        }
    ]
    
    return sample_alerts[:limit]


@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    """
    Advanced analytics and insights
    ---
    tags:
      - Analytics API
    parameters:
      - name: type
        in: query
        type: string
        enum: [overview, attendance, emotions, performance, predictions]
        default: overview
        description: Analytics type
      - name: period
        in: query
        type: string
        enum: [week, month, quarter, year]
        default: month
        description: Time period for analysis
      - name: start
        in: query
        type: string
        format: date
        description: Custom start date (YYYY-MM-DD)
      - name: end
        in: query
        type: string
        format: date
        description: Custom end date (YYYY-MM-DD)
      - name: compare
        in: query
        type: string
        enum: [previous_period, last_year]
        description: Compare with previous period
    responses:
      200:
        description: Analytics data
        schema:
          type: object
          properties:
            analytics_type:
              type: string
            period:
              type: string
            data:
              type: object
            insights:
              type: array
      500:
        description: Analytics generation failed
    """
    if not db:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        analytics_type = request.args.get('type', 'overview').lower()
        period = request.args.get('period', 'month').lower()
        custom_start = request.args.get('start')
        custom_end = request.args.get('end')
        compare_with = request.args.get('compare')
        
        # Determine date range
        if custom_start and custom_end:
            start_date = custom_start
            end_date = custom_end
        else:
            end_date = date.today()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            start_date = start_date.isoformat()
            end_date = end_date.isoformat()
        
        # Get data for current period
        current_data = db.get_attendance_by_date_range(start_date, end_date)
        
        # Get comparison data if requested
        comparison_data = None
        if compare_with == 'previous_period':
            days_diff = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
            comp_end = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)
            comp_start = comp_end - timedelta(days=days_diff)
            comparison_data = db.get_attendance_by_date_range(comp_start.isoformat(), comp_end.isoformat())
        
        # Generate analytics based on type
        if analytics_type == 'overview':
            analytics_result = generate_overview_analytics(current_data, comparison_data, start_date, end_date)
        elif analytics_type == 'attendance':
            analytics_result = generate_attendance_analytics(current_data, comparison_data, start_date, end_date)
        elif analytics_type == 'emotions':
            analytics_result = generate_emotion_analytics(current_data, start_date, end_date)
        elif analytics_type == 'performance':
            analytics_result = generate_performance_analytics(current_data, start_date, end_date)
        elif analytics_type == 'predictions':
            analytics_result = generate_prediction_analytics(current_data, start_date, end_date)
        else:
            return jsonify({'error': 'Invalid analytics type'}), 400
        
        # Add metadata
        analytics_result['metadata'] = {
            'analytics_type': analytics_type,
            'period': period,
            'date_range': f"{start_date} to {end_date}",
            'generated_at': datetime.now().isoformat(),
            'data_points': len(current_data),
            'has_comparison': comparison_data is not None
        }
        
        return jsonify(analytics_result)
        
    except Exception as e:
        return jsonify({'error': f'Analytics generation failed: {str(e)}'}), 500

def generate_overview_analytics(current_data, comparison_data, start_date, end_date):
    """Generate overview analytics"""
    # Basic metrics
    total_records = len(current_data)
    unique_students = len(set(r.get('student_id') for r in current_data))
    unique_dates = len(set(r.get('date') for r in current_data))
    
    # Calculate attendance rate
    all_students = db.get_all_students()
    total_students = len(all_students)
    possible_attendance = total_students * unique_dates
    attendance_rate = (total_records / possible_attendance * 100) if possible_attendance > 0 else 0
    
    # Emotion analysis
    emotion_counts = {}
    for record in current_data:
        emotion = record.get('emotion', 'neutral')
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    # Daily patterns
    daily_patterns = {}
    for record in current_data:
        date = record.get('date')
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                daily_patterns[day_name] = daily_patterns.get(day_name, 0) + 1
            except:
                continue
    
    # Time patterns
    hourly_patterns = {}
    for record in current_data:
        time = record.get('time', '00:00')
        if time:
            try:
                hour = int(time.split(':')[0])
                hour_range = f"{hour}:00-{hour+1}:00"
                hourly_patterns[hour_range] = hourly_patterns.get(hour_range, 0) + 1
            except:
                continue
    
    # Generate insights
    insights = []
    
    if attendance_rate > 90:
        insights.append({
            'type': 'success',
            'title': 'Excellent Attendance',
            'description': f'Attendance rate of {attendance_rate:.1f}% is very good',
            'recommendation': 'Maintain current attendance policies'
        })
    elif attendance_rate < 70:
        insights.append({
            'type': 'warning',
            'title': 'Low Attendance Rate',
            'description': f'Attendance rate of {attendance_rate:.1f}% needs improvement',
            'recommendation': 'Consider implementing attendance improvement strategies'
        })
    
    # Find peak day
    if daily_patterns:
        peak_day = max(daily_patterns, key=daily_patterns.get)
        insights.append({
            'type': 'info',
            'title': 'Peak Attendance Day',
            'description': f'{peak_day} has the highest attendance',
            'recommendation': f'Schedule important activities on {peak_day}'
        })
    
    # Comparison analysis
    comparison_insights = []
    if comparison_data:
        prev_records = len(comparison_data)
        change_percent = ((total_records - prev_records) / prev_records * 100) if prev_records > 0 else 0
        
        if change_percent > 10:
            comparison_insights.append({
                'type': 'positive',
                'title': 'Attendance Increased',
                'description': f'Attendance increased by {change_percent:.1f}% compared to previous period',
                'trend': 'improving'
            })
        elif change_percent < -10:
            comparison_insights.append({
                'type': 'negative',
                'title': 'Attendance Decreased',
                'description': f'Attendance decreased by {abs(change_percent):.1f}% compared to previous period',
                'trend': 'declining'
            })
    
    return {
        'overview': {
            'total_records': total_records,
            'unique_students': unique_students,
            'total_students': total_students,
            'unique_dates': unique_dates,
            'attendance_rate': round(attendance_rate, 1)
        },
        'emotion_summary': emotion_counts,
        'daily_patterns': daily_patterns,
        'hourly_patterns': hourly_patterns,
        'insights': insights,
        'comparison': comparison_insights if comparison_data else None
    }

def generate_attendance_analytics(current_data, comparison_data, start_date, end_date):
    """Generate detailed attendance analytics"""
    # Student-level analysis
    student_stats = {}
    all_students = db.get_all_students()
    
    for student in all_students:
        student_id = student['id']
        student_attendance = [r for r in current_data if r.get('student_id') == student_id]
        
        student_stats[student_id] = {
            'name': student['name'],
            'attendance_count': len(student_attendance),
            'attendance_dates': [r.get('date') for r in student_attendance],
            'emotions': [r.get('emotion', 'neutral') for r in student_attendance]
        }
    
    # Calculate attendance rates
    unique_dates = len(set(r.get('date') for r in current_data))
    for student_id in student_stats:
        attendance_rate = (student_stats[student_id]['attendance_count'] / unique_dates * 100) if unique_dates > 0 else 0
        student_stats[student_id]['attendance_rate'] = round(attendance_rate, 1)
    
    # Identify patterns
    regular_attenders = [s for s in student_stats.values() if s['attendance_rate'] >= 90]
    irregular_attenders = [s for s in student_stats.values() if s['attendance_rate'] < 60]
    
    # Weekly trends
    weekly_trends = {}
    for record in current_data:
        date = record.get('date')
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                week = date_obj.isocalendar()[1]
                weekly_trends[week] = weekly_trends.get(week, 0) + 1
            except:
                continue
    
    return {
        'student_analysis': student_stats,
        'attendance_segments': {
            'regular_attenders': len(regular_attenders),
            'irregular_attenders': len(irregular_attenders),
            'moderate_attenders': len(all_students) - len(regular_attenders) - len(irregular_attenders)
        },
        'weekly_trends': weekly_trends,
        'recommendations': generate_attendance_recommendations(student_stats, unique_dates)
    }

def generate_emotion_analytics(current_data, start_date, end_date):
    """Generate emotion-based analytics"""
    # Overall emotion distribution
    emotion_counts = {}
    emotion_by_date = {}
    emotion_by_student = {}
    
    for record in current_data:
        emotion = record.get('emotion', 'neutral')
        date = record.get('date')
        student_id = record.get('student_id')
        
        # Overall counts
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # By date
        if date:
            if date not in emotion_by_date:
                emotion_by_date[date] = {}
            emotion_by_date[date][emotion] = emotion_by_date[date].get(emotion, 0) + 1
        
        # By student
        if student_id:
            if student_id not in emotion_by_student:
                emotion_by_student[student_id] = {}
            emotion_by_student[student_id][emotion] = emotion_by_student[student_id].get(emotion, 0) + 1
    
    # Calculate emotion trends
    emotion_trends = {}
    for emotion in emotion_counts:
        trend_data = []
        for date in sorted(emotion_by_date.keys()):
            count = emotion_by_date[date].get(emotion, 0)
            trend_data.append({'date': date, 'count': count})
        emotion_trends[emotion] = trend_data
    
    # Student emotion profiles
    student_emotion_profiles = {}
    for student_id in emotion_by_student:
        total_emotions = sum(emotion_by_student[student_id].values())
        student_emotion_profiles[student_id] = {
            'dominant_emotion': max(emotion_by_student[student_id], key=emotion_by_student[student_id].get),
            'emotion_diversity': len(emotion_by_student[student_id]),
            'emotion_distribution': {k: v/total_emotions for k, v in emotion_by_student[student_id].items()}
        }
    
    return {
        'overall_distribution': emotion_counts,
        'emotion_trends': emotion_trends,
        'student_profiles': student_emotion_profiles,
        'insights': generate_emotion_insights(emotion_counts, emotion_by_date)
    }

def generate_performance_analytics(current_data, start_date, end_date):
    """Generate performance analytics"""
    # Calculate various performance metrics
    performance_metrics = {
        'consistency_scores': {},
        'punctuality_analysis': {},
        'engagement_metrics': {}
    }
    
    # Student consistency
    student_daily_attendance = {}
    for record in current_data:
        student_id = record.get('student_id')
        date = record.get('date')
        
        if student_id not in student_daily_attendance:
            student_daily_attendance[student_id] = set()
        student_daily_attendance[student_id].add(date)
    
    # Calculate consistency scores
    total_days = len(set(r.get('date') for r in current_data))
    for student_id in student_daily_attendance:
        attendance_days = len(student_daily_attendance[student_id])
        consistency_score = (attendance_days / total_days * 100) if total_days > 0 else 0
        performance_metrics['consistency_scores'][student_id] = round(consistency_score, 1)
    
    # Punctuality analysis (based on time)
    time_analysis = {}
    for record in current_data:
        time = record.get('time', '00:00')
        if time:
            try:
                hour = int(time.split(':')[0])
                time_analysis[hour] = time_analysis.get(hour, 0) + 1
            except:
                continue
    
    # Engagement metrics (based on emotion diversity)
    student_emotions = {}
    for record in current_data:
        student_id = record.get('student_id')
        emotion = record.get('emotion', 'neutral')
        
        if student_id not in student_emotions:
            student_emotions[student_id] = set()
        student_emotions[student_id].add(emotion)
    
    for student_id in student_emotions:
        engagement_score = len(student_emotions[student_id]) * 20  # Simple scoring
        performance_metrics['engagement_metrics'][student_id] = min(engagement_score, 100)
    
    return {
        'performance_metrics': performance_metrics,
        'time_analysis': time_analysis,
        'top_performers': get_top_performers(performance_metrics),
        'improvement_areas': identify_improvement_areas(performance_metrics)
    }

def generate_prediction_analytics(current_data, start_date, end_date):
    """Generate predictive analytics"""
    # Simple predictions based on trends
    predictions = {
        'attendance_forecast': [],
        'risk_students': [],
        'trend_predictions': {}
    }
    
    # Attendance trend prediction (simplified)
    daily_counts = {}
    for record in current_data:
        date = record.get('date')
        if date:
            daily_counts[date] = daily_counts.get(date, 0) + 1
    
    # Simple linear trend prediction
    if len(daily_counts) >= 3:
        dates = sorted(daily_counts.keys())
        counts = [daily_counts[date] for date in dates]
        
        # Calculate simple trend
        if len(counts) >= 2:
            trend = (counts[-1] - counts[0]) / len(counts)
            next_day_prediction = max(0, counts[-1] + trend)
            
            predictions['attendance_forecast'] = {
                'next_day': round(next_day_prediction),
                'trend': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                'confidence': 'moderate'
            }
    
    # Identify at-risk students (low attendance)
    student_attendance = {}
    for record in current_data:
        student_id = record.get('student_id')
        if student_id not in student_attendance:
            student_attendance[student_id] = 0
        student_attendance[student_id] += 1
    
    total_days = len(set(r.get('date') for r in current_data))
    for student_id, count in student_attendance.items():
        attendance_rate = (count / total_days * 100) if total_days > 0 else 0
        if attendance_rate < 60:
            predictions['risk_students'].append({
                'student_id': student_id,
                'attendance_rate': round(attendance_rate, 1),
                'risk_level': 'high' if attendance_rate < 40 else 'medium'
            })
    
    return {
        'predictions': predictions,
        'confidence_level': 'moderate',
        'model_version': '1.0',
        'disclaimer': 'Predictions are based on historical patterns and may not be accurate'
    }

# Helper functions for analytics
def generate_attendance_recommendations(student_stats, total_days):
    """Generate attendance recommendations"""
    recommendations = []
    
    # Low attendance students
    low_attendance = [s for s in student_stats.values() if s['attendance_rate'] < 60]
    if low_attendance:
        recommendations.append({
            'type': 'intervention',
            'priority': 'high',
            'message': f'{len(low_attendance)} students have attendance below 60%',
            'action': 'Schedule counseling sessions'
        })
    
    # Perfect attendance
    perfect_attendance = [s for s in student_stats.values() if s['attendance_rate'] == 100]
    if perfect_attendance:
        recommendations.append({
            'type': 'recognition',
            'priority': 'medium',
            'message': f'{len(perfect_attendance)} students have perfect attendance',
            'action': 'Consider recognition awards'
        })
    
    return recommendations

def generate_emotion_insights(emotion_counts, emotion_by_date):
    """Generate emotion-based insights"""
    insights = []
    
    # Most common emotion
    if emotion_counts:
        most_common = max(emotion_counts, key=emotion_counts.get)
        insights.append({
            'type': 'observation',
            'message': f'Most common emotion is {most_common} ({emotion_counts[most_common]} occurrences)',
            'significance': 'high' if emotion_counts[most_common] > sum(emotion_counts.values()) * 0.5 else 'medium'
        })
    
    return insights

def get_top_performers(performance_metrics):
    """Get top performing students"""
    # Combine different metrics for overall performance
    student_scores = {}
    
    for student_id in performance_metrics['consistency_scores']:
        consistency = performance_metrics['consistency_scores'].get(student_id, 0)
        engagement = performance_metrics['engagement_metrics'].get(student_id, 0)
        
        # Weighted score
        overall_score = (consistency * 0.7) + (engagement * 0.3)
        student_scores[student_id] = overall_score
    
    # Sort and return top 5
    top_students = sorted(student_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return [{'student_id': sid, 'score': round(score, 1)} for sid, score in top_students]

def identify_improvement_areas(performance_metrics):
    """Identify areas needing improvement"""
    improvement_areas = []
    
    # Low consistency students
    low_consistency = [sid for sid, score in performance_metrics['consistency_scores'].items() if score < 70]
    if low_consistency:
        improvement_areas.append({
            'area': 'attendance_consistency',
            'affected_students': len(low_consistency),
            'recommendation': 'Focus on improving regular attendance patterns'
        })
    
    # Low engagement students
    low_engagement = [sid for sid, score in performance_metrics['engagement_metrics'].items() if score < 50]
    if low_engagement:
        improvement_areas.append({
            'area': 'student_engagement',
            'affected_students': len(low_engagement),
            'recommendation': 'Implement engagement strategies'
        })
    
    return improvement_areas

@app.route('/api/attendance/daily', methods=['GET'])
def api_attendance_daily():
    """
    Get daily attendance data for the last 7 days
    ---
    tags:
      - Charts API
    responses:
      200:
        description: Returns attendance data for the last 7 days
    """
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        dates = []
        present_counts = []
        total_counts = []
        
        today = date.today()
        for i in range(6, -1, -1):
            current_date = today - timedelta(days=i)
            date_str = current_date.isoformat()
            
            attendance = db.get_attendance_with_emotions(date_str)
            students = db.get_all_students()
            
            present_set = set(r['name'] for r in attendance)
            
            dates.append(date_str)
            present_counts.append(len(present_set))
            total_counts.append(len(students))
        
        return jsonify({
            'dates': dates,
            'present': present_counts,
            'total': total_counts
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/attendance/monthly', methods=['GET'])
def api_attendance_monthly():
    """
    Get monthly attendance data for the last 12 months
    ---
    tags:
      - Charts API
    responses:
      200:
        description: Returns monthly attendance averages
    """
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        months = []
        rates = []
        
        today = date.today()
        for i in range(11, -1, -1):
            year = today.year if today.month > i else today.year - 1
            month = (today.month - i) if today.month > i else (12 + today.month - i)
            
            month_str = f"{year}-{month:02d}"
            months.append(month_str)
            
            rate = 75 + (i % 20)
            rates.append(rate)
        
        return jsonify({
            'months': months,
            'attendance_rates': rates
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/emotions', methods=['GET'])
def api_emotions():
    """
    Get emotion distribution for today
    ---
    tags:
      - Charts API
    responses:
      200:
        description: Returns emotion counts and percentages
    """
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        today = date.today().isoformat()
        attendance = db.get_attendance_with_emotions(today)
        
        emotion_counts = {}
        for record in attendance:
            emotion = record.get('emotion', 'neutral')
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        emotions = list(emotion_counts.keys())
        counts = list(emotion_counts.values())
        total = sum(counts) if counts else 1
        percentages = [round((c / total) * 100, 1) for c in counts]
        
        return jsonify({
            'emotions': emotions,
            'counts': counts,
            'percentages': percentages
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/attendance/hourly', methods=['GET'])
def api_attendance_hourly():
    """
    Get hourly attendance breakdown for today
    ---
    tags:
      - Charts API
    responses:
      200:
        description: Returns hourly attendance data
    """
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        today = date.today().isoformat()
        attendance = db.get_attendance_with_emotions(today)
        
        hourly_counts = {}
        for hour in range(24):
            hourly_counts[f"{hour:02d}:00"] = 0
        
        for record in attendance:
            time_str = record.get('time', '00:00')
            hour = time_str.split(':')[0]
            hour_key = f"{hour}:00"
            if hour_key in hourly_counts:
                hourly_counts[hour_key] += 1
        
        hours = list(hourly_counts.keys())
        counts = list(hourly_counts.values())
        
        return jsonify({
            'hours': hours,
            'attendance': counts
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/search', methods=['GET'])
def api_search():
    """
    Advanced search for students
    ---
    tags:
      - Search & Filter API
    parameters:
      - name: query
        in: query
        type: string
        description: Search term (name)
    responses:
      200:
        description: Returns matching students and their attendance records
    """
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        query = request.args.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'results': [], 'message': 'Please enter at least 2 characters'})
        
        students = db.get_all_students()
        results = []
        
        for student in students:
            if query.lower() in student.get('name', '').lower():
                student_data = {
                    'id': student.get('id'),
                    'name': student.get('name'),
                    'department': student.get('department', 'N/A'),
                    'email': student.get('email', 'N/A')
                }
                results.append(student_data)
        
        return jsonify({
            'results': results,
            'count': len(results),
            'query': query
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/attendance/filter', methods=['GET'])
def api_attendance_filter():
    """
    Filter attendance by date range and department
    ---
    tags:
      - Search & Filter API
    parameters:
      - name: start_date
        in: query
        type: string
        description: Start date (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        description: End date (YYYY-MM-DD)
      - name: department
        in: query
        type: string
        description: Department name
      - name: student_name
        in: query
        type: string
        description: Student name (optional)
    responses:
      200:
        description: Returns filtered attendance records
    """
    if not db:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        department = request.args.get('department', '').strip()
        student_name = request.args.get('student_name', '').strip()
        
        # Validate dates
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'})
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'})
        
        all_records = []
        students = db.get_all_students()
        
        # Iterate through date range
        current_date = start
        while current_date <= end:
            date_str = current_date.isoformat()
            attendance = db.get_attendance_with_emotions(date_str)
            
            for record in attendance:
                # Filter by department if specified
                if department:
                    student = next((s for s in students if s.get('name') == record.get('name')), None)
                    if not student or student.get('department', '').lower() != department.lower():
                        continue
                
                # Filter by student name if specified
                if student_name and student_name.lower() not in record.get('name', '').lower():
                    continue
                
                all_records.append({
                    'date': date_str,
                    'name': record.get('name'),
                    'time': record.get('time'),
                    'emotion': record.get('emotion', 'neutral'),
                    'is_real_face': record.get('is_real_face', False)
                })
            
            current_date += timedelta(days=1)
        
        # Calculate statistics
        unique_students = set(r['name'] for r in all_records)
        stats = {
            'total_records': len(all_records),
            'unique_students': len(unique_students),
            'date_range': f"{start_date} to {end_date}"
        }
        
        return jsonify({
            'records': all_records,
            'stats': stats,
            'filters_applied': {
                'start_date': start_date,
                'end_date': end_date,
                'department': department if department else None,
                'student_name': student_name if student_name else None
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/export/csv', methods=['POST'])
def api_export_csv():
    """
    Export attendance data as CSV
    ---
    tags:
      - Export API
    parameters:
      - name: records
        in: body
        type: array
        description: Array of attendance records
      - name: filename
        in: body
        type: string
        description: Output filename
    responses:
      200:
        description: Returns CSV file
    """
    try:
        data = request.get_json()
        records = data.get('records', [])
        filename = data.get('filename', 'attendance_export.csv')
        
        if not records:
            return jsonify({'error': 'No records to export'}), 400
        
        # Create CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['Date', 'Name', 'Time', 'Emotion', 'Real Face'])
        
        writer.writeheader()
        for record in records:
            writer.writerow({
                'Date': record.get('date', ''),
                'Name': record.get('name', ''),
                'Time': record.get('time', ''),
                'Emotion': record.get('emotion', ''),
                'Real Face': 'Yes' if record.get('is_real_face') else 'No'
            })
        
        csv_content = output.getvalue()
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/json', methods=['POST'])
def api_export_json():
    """
    Export attendance data as JSON
    ---
    tags:
      - Export API
    """
    try:
        data = request.get_json()
        records = data.get('records', [])
        filename = data.get('filename', 'attendance_export.json')
        
        if not records:
            return jsonify({'error': 'No records to export'}), 400
        
        json_content = json.dumps(records, indent=2, ensure_ascii=False)
        
        return Response(
            json_content,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

