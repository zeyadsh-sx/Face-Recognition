#!/usr/bin/env python3
"""
Startup script for MySQL Face Recognition System
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mysql_config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT
    from gui_simple_mysql import SimpleMySQLAttendanceGUI
    
    print("[INFO] Starting Advanced Face Recognition System (MySQL)...")
    print("[DB] Connected to MySQL database")
    print("[AI] Advanced features enabled: Anti-spoofing, Emotion Detection, Unknown Face Alerts")
    print("=" * 60)
    
    # Create application with MySQL configuration
    app = SimpleMySQLAttendanceGUI({
        'host': MYSQL_HOST,
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'database': MYSQL_DATABASE,
        'port': MYSQL_PORT
    })
    
    app.run()
    
except ImportError as e:
    print(f"[ERROR] Import Error: {e}")
    print("Please run setup_mysql.py first to configure MySQL")
    sys.exit(1)
    
except Exception as e:
    print(f"[ERROR] Error starting application: {e}")
    sys.exit(1)
