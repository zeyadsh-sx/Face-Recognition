#!/usr/bin/env python3
"""
<<<<<<< HEAD
MySQL GUI Application Startup Script for Advanced Face Recognition System
=======
Startup script for MySQL Face Recognition System
>>>>>>> 0ff114af8d6095d7552fa329158b80fa8261a7c5
"""

import sys
import os
<<<<<<< HEAD
import subprocess
import time
from pathlib import Path
=======
>>>>>>> 0ff114af8d6095d7552fa329158b80fa8261a7c5

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

<<<<<<< HEAD
def print_menu():
    """Print main menu"""
    print("\n" + "=" * 70)
    print("🎯 ADVANCED FACE RECOGNITION ATTENDANCE SYSTEM - MySQL Edition")
    print("=" * 70)
    print("\n📋 SELECT AN OPTION:")
    print("-" * 70)
    print("1️⃣  🖥️  GUI Application (Tkinter - LOCAL)")
    print("2️⃣  🌐 Web Dashboard (Flask - REMOTE)")
    print("3️⃣  📡 Face Recognition System (Real-time)")
    print("4️⃣  🔧 Setup MySQL Database")
    print("5️⃣  ❌ Exit")
    print("-" * 70)
    return input("\n🔹 Choose an option (1-5): ").strip()

def check_mysql_running():
    """Check if MySQL server is running"""
    try:
        from database_core_mysql import MySQLAttendanceDatabase
        db = MySQLAttendanceDatabase()
        if db.test_connection():
            print("✅ MySQL server is running and accessible!")
            return True
    except Exception as e:
        print(f"❌ MySQL server error: {e}")
        return False

def run_gui():
    """Run GUI Application"""
    print("\n🖥️  Starting GUI Application...")
    print("=" * 70)
    print("Loading MySQL GUI interface...")
    time.sleep(1)
    
    try:
        from gui_basic_mysql import BasicMySQLAttendanceGUI
        gui = BasicMySQLAttendanceGUI()
        gui.root.mainloop()
    except Exception as e:
        print(f"❌ GUI Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Check database connection settings in database_core_mysql.py")
        print("3. Ensure all required libraries are installed")
        input("\nPress Enter to return to menu...")

def run_dashboard():
    """Run Flask Web Dashboard"""
    print("\n🌐 Starting Web Dashboard...")
    print("=" * 70)
    print("Initializing Flask server on http://localhost:5000")
    time.sleep(1)
    
    try:
        # Run the launcher script
        subprocess.run([sys.executable, "launcher_dashboard_mysql.py"])
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure ports 5000 is not in use")
        print("2. Check if MySQL server is running")
        print("3. Verify Flask and flasgger are installed")
        input("\nPress Enter to return to menu...")

def run_face_recognition():
    """Run Face Recognition System"""
    print("\n📡 Starting Face Recognition System...")
    print("=" * 70)
    print("Initializing camera and AI models...")
    time.sleep(1)
    
    try:
        from features_ai_advanced import FaceRecognitionSystem
        system = FaceRecognitionSystem()
        system.run()
    except Exception as e:
        print(f"❌ Face Recognition Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure camera is connected and accessible")
        print("2. Check if face_recognition and cv2 are properly installed")
        print("3. Verify MySQL server is running")
        input("\nPress Enter to return to menu...")

def setup_database():
    """Setup MySQL Database"""
    print("\n🔧 Setting up MySQL Database...")
    print("=" * 70)
    
    try:
        subprocess.run([sys.executable, "setup_database_mysql.py"])
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        input("\nPress Enter to return to menu...")

def main():
    """Main application loop"""
    print("\n✅ Application Starting...")
    print("Checking dependencies...")
    time.sleep(1)
    
    while True:
        choice = print_menu()
        
        if choice == '1':
            print("\n🔍 Checking MySQL connection...")
            if check_mysql_running():
                run_gui()
            else:
                print("\n⚠️  Could not connect to MySQL server!")
                print("Please start MySQL server and try again.")
                input("\nPress Enter to return to menu...")
        
        elif choice == '2':
            print("\n🔍 Checking MySQL connection...")
            if check_mysql_running():
                run_dashboard()
            else:
                print("\n⚠️  Could not connect to MySQL server!")
                print("Please start MySQL server and try again.")
                input("\nPress Enter to return to menu...")
        
        elif choice == '3':
            print("\n🔍 Checking MySQL connection...")
            if check_mysql_running():
                run_face_recognition()
            else:
                print("\n⚠️  Could not connect to MySQL server!")
                print("Please start MySQL server and try again.")
                input("\nPress Enter to return to menu...")
        
        elif choice == '4':
            setup_database()
        
        elif choice == '5':
            print("\n👋 Thanks for using the Advanced Face Recognition System!")
            print("Goodbye! 🚀")
            break
        
        else:
            print("❌ Invalid choice! Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Application interrupted by user.")
        print("Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
=======
try:
    from mysql_config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT
    from gui_simple_mysql import SimpleMySQLAttendanceGUI
    
    print("🚀 Starting Advanced Face Recognition System (MySQL)...")
    print("📊 Connected to MySQL database")
    print("🔒 Advanced features enabled: Anti-spoofing, Emotion Detection, Unknown Face Alerts")
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
    print(f"❌ Import Error: {e}")
    print("Please run setup_mysql.py first to configure MySQL")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error starting application: {e}")
    sys.exit(1)
>>>>>>> 0ff114af8d6095d7552fa329158b80fa8261a7c5
