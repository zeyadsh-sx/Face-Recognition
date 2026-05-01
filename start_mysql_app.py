#!/usr/bin/env python3
"""
Startup script for MySQL Face Recognition System
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import mysql_config
    try:
        from mysql_config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT
        from gui_basic_mysql import BasicMySQLAttendanceGUI
        
        print("🚀 Starting Advanced Face Recognition System (MySQL)...")
        print("📊 Connected to MySQL database")
        print("🔒 Advanced features enabled: Anti-spoofing, Emotion Detection, Unknown Face Alerts")
        print("=" * 60)
        
        # Create application with MySQL configuration
        app = BasicMySQLAttendanceGUI({
            'host': MYSQL_HOST,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'database': MYSQL_DATABASE,
            'port': MYSQL_PORT
        })
        
        app.run()
        
    except ImportError as config_error:
        print(f"⚠️ Configuration error: {config_error}")
        print("🔧 Creating default configuration...")
        
        # Create default configuration
        default_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'attendance_system',
            'port': 3306
        }
        
        try:
            from gui_basic_mysql import BasicMySQLAttendanceGUI
            app = BasicMySQLAttendanceGUI(default_config)
            app.run()
        except ImportError as gui_error:
            print(f"❌ GUI import error: {gui_error}")
            print("💡 Please run: python setup_database_mysql.py")
            sys.exit(1)
            
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Please install required packages:")
    print("   pip install mysql-connector-python")
    print("   pip install opencv-python")
    print("   pip install face-recognition")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error starting application: {e}")
    print("💡 Please check MySQL connection and try again")
    sys.exit(1)
