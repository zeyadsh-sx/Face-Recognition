from flask import Flask, Response
import json
from datetime import datetime, date, timedelta
import os
from database_core_mysql import MySQLAttendanceDatabase

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize MySQL database
try:
    db = MySQLAttendanceDatabase()
    print("✅ MySQL Dashboard connected successfully!")
except Exception as e:
    print(f"❌ MySQL Dashboard connection failed: {e}")
    db = None

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

def generate_dashboard_html(stats, attendance_records):
    """Generate dashboard HTML directly"""
    
    # Generate emotion summary HTML
    emotion_html = ""
    if stats['emotion_summary']:
        for emotion, count in stats['emotion_summary'].items():
            emotion_html += f'<div class="d-flex justify-content-between mb-2"><span>{emotion.capitalize()}</span><span class="badge bg-primary">{count}</span></div>'
    else:
        emotion_html = '<p class="text-muted">No emotion data available</p>'
    
    # Generate attendance table HTML
    attendance_html = ""
    if attendance_records:
        for record in attendance_records:
            emotion_badge = f'<span class="badge bg-info">{record["emotion"]}</span>' if record.get('emotion') else '<span class="text-muted">N/A</span>'
            real_face_icon = '<i class="bi bi-check-circle text-success"></i>' if record.get('is_real_face') else '<i class="bi bi-x-circle text-danger"></i>'
            
            attendance_html += f"""
            <tr>
                <td>{record['name']}</td>
                <td>{record['time']}</td>
                <td>{emotion_badge}</td>
                <td>{real_face_icon}</td>
            </tr>
            """
    else:
        attendance_html = '<div class="text-center py-4"><i class="bi bi-calendar-x fs-1 text-muted"></i><p class="text-muted mt-2">No attendance records for today</p></div>'
    
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MySQL Dashboard - Advanced Attendance System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .navbar {{
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px);
        }}
        .card {{
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
        }}
        .stat-card {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }}
        .badge-success {{
            background: linear-gradient(45deg, #28a745, #20c997) !important;
        }}
    </style>
</head>

<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-database"></i>
                MySQL Advanced Attendance Dashboard
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">
                    <i class="bi bi-wifi text-success"></i>
                    <span class="badge bg-success ms-2">Connected</span>
                </span>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container-fluid p-4">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <h2>
                        <i class="bi bi-speedometer2"></i>
                        MySQL Dashboard
                    </h2>
                    <div class="text-muted">
                        <i class="bi bi-clock"></i>
                        <span id="current-time"></span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Statistics Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stat-card text-white">
                    <div class="card-body">
                        <h4 class="card-title">{stats['total_students']}</h4>
                        <p class="card-text">Total Students</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card text-white">
                    <div class="card-body">
                        <h4 class="card-title">{stats['present_students']}</h4>
                        <p class="card-text">Present Today</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card text-white">
                    <div class="card-body">
                        <h4 class="card-title">{stats['absent_students']}</h4>
                        <p class="card-text">Absent Today</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card text-white">
                    <div class="card-body">
                        <h4 class="card-title">{stats['attendance_rate']}%</h4>
                        <p class="card-text">Attendance Rate</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Additional Info -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="bi bi-emoji-smile"></i> Emotion Summary</h5>
                    </div>
                    <div class="card-body">
                        {emotion_html}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="bi bi-shield-exclamation"></i> Security Alerts</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Active Alerts:</strong> {stats['active_alerts']}</p>
                        <p><strong>System Status:</strong> <span class="badge bg-success">Operational</span></p>
                        <p><strong>Last Update:</strong> {stats['date']}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Today's Attendance -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between">
                        <h5><i class="bi bi-calendar-check"></i> Today's Attendance</h5>
                        <button class="btn btn-sm btn-outline-primary" onclick="refreshData()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        {attendance_html}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Update current time
        function updateTime() {{
            const now = new Date();
            const timeString = now.toLocaleTimeString('ar-SA', {{ 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            }});
            document.getElementById('current-time').textContent = timeString;
        }}

        // Refresh data function
        function refreshData() {{
            window.location.reload();
        }}

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {{
            updateTime();
            setInterval(updateTime, 1000);
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        }});
    </script>
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

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
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

if __name__ == '__main__':
    print("🚀 Starting Final MySQL Dashboard...")
    print("📊 Connected to MySQL database")
    print("🌐 Dashboard will be available at: http://localhost:5000")
    print("=" * 50)
    print("📱 Mobile friendly - works on phones and tablets")
    print("🔄 Auto-refresh every 30 seconds")
    print("📈 Real-time analytics from MySQL database")
    print("=" * 50)
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    
