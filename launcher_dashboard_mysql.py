#!/usr/bin/env python3
"""
MySQL Dashboard Startup Script for Advanced Face Recognition System
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🚀 Starting MySQL Dashboard...")
    print("📊 Connecting to MySQL database...")
    print("🌐 Dashboard will be available at: http://localhost:5000")
    print("=" * 60)
    
    # Import and run the MySQL dashboard
    from dashboard_web_standalone import app
    
    print("✅ MySQL Dashboard connected successfully!")
    print("🔒 Advanced features enabled: Anti-spoofing, Emotion Detection, Unknown Face Alerts")
    print("📈 Real-time analytics from MySQL database")
    print("=" * 60)
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("📱 Mobile friendly - works on phones and tablets")
    print("🔄 Auto-refresh every 30 seconds")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please make sure all required files are present:")
    print("- dashboard_mysql.py")
    print("- database_mysql.py")
    print("- advanced_features.py")
    print("Also ensure MySQL connector is installed: pip install mysql-connector-python")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error starting MySQL dashboard: {e}")
    print("Please check:")
    print("1. MySQL server is running")
    print("2. Database connection is configured")
    print("3. All required files are present")
    sys.exit(1)
