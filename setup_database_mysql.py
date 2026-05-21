#!/usr/bin/env python3
"""
MySQL Database Setup Script for Advanced Face Recognition Attendance System
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.database_core_mysql import MySQLAttendanceDatabase

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("Advanced Face Recognition - MySQL Setup")
    print("=" * 60)
    print("This script will help you set up MySQL database for the")
    print("Advanced Face Recognition Attendance System.")
    print("=" * 60)

def check_mysql_driver():
    """Check if MySQL driver is installed"""
    try:
        import mysql.connector
        print("MySQL connector is installed")
        return True
    except ImportError:
        print("MySQL connector is not installed")
        print("Please install it with: pip install mysql-connector-python")
        return False

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    
    requirements = [
        'mysql-connector-python==8.1.0',
        'face-recognition==1.3.0',
        'opencv-python==4.8.1.78',
        'numpy==1.24.3',
        'Pillow==10.0.0'
    ]
    
    for package in requirements:
        print(f"Installing {package}...")
        os.system(f"pip install {package}")
    
    print("All packages installed successfully!")

def test_mysql_connection():
    """Test MySQL connection with user input"""
    print("🔗 Testing MySQL connection...")
    
    # Use default XAMPP settings
    host = 'localhost'
    user = 'root'
    password = ''
    database = 'attendance_system'
    port = 3306
    
    try:
        db = MySQLAttendanceDatabase(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        print("MySQL connection successful!")
        return db, {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port
        }
    except Exception as e:
        print(f"Connection failed: {e}")
        print("💡 Using default XAMPP settings...")
        print("   Host: localhost")
        print("   User: root")
        print("   Password: (empty)")
        print("   Database: attendance_system")
        return None, {}

def save_config(host, user, password, database, port):
    """Save MySQL configuration to file"""
    config_content = f"""# MySQL Configuration for Face Recognition System
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

MYSQL_HOST = "{host}"
MYSQL_USER = "{user}"
MYSQL_PASSWORD = "{password}"
MYSQL_DATABASE = "{database}"
MYSQL_PORT = {port}

# Use this configuration in your application
from core.database_core_mysql import MySQLAttendanceDatabase

db = MySQLAttendanceDatabase(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
    port=MYSQL_PORT
)
"""
    
    with open('mysql_config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("Configuration saved to 'mysql_config.py'")

def migrate_existing_data():
    """Migrate existing SQLite data to MySQL"""
    if os.path.exists("attendance_system.db"):
        migrate = input("\n Found SQLite database. Migrate to MySQL? (y/n): ").strip().lower()
        if migrate == 'y':
            print("Migrating SQLite data to MySQL...")
            
            try:
                # Get MySQL configuration again
                host = input("Enter MySQL host: ").strip() or 'localhost'
                user = input("Enter MySQL username: ").strip() or 'root'
                password = input("Enter MySQL password: ").strip()
                database = input("Enter MySQL database: ").strip() or 'attendance_system'
                port = input("Enter MySQL port: ").strip()
                port = int(port) if port else 3306
                
                db = MySQLAttendanceDatabase(host=host, user=user, password=password, 
                                            database=database, port=port)
                
                success = db.migrate_from_sqlite("attendance_system.db")
                
                if success:
                    print("Migration completed successfully!")
                    # Backup old SQLite database
                    os.rename("attendance_system.db", "attendance_system.db.backup")
                    print("SQLite database backed up as 'attendance_system.db.backup'")
                else:
                    print("Migration failed!")
                    
            except Exception as e:
                print(f"Migration error: {e}")
    else:
        print("No existing SQLite database found")

def create_startup_script():
    """Create startup script for MySQL application"""
    startup_content = '''#!/usr/bin/env python3
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
'''
    
    with open('start_mysql_app.py', 'w', encoding='utf-8') as f:
        f.write(startup_content)
    
    print("Startup script created: 'start_mysql_app.py'")

def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    if not check_mysql_driver():
        install = input("Install MySQL connector now? (y/n): ").strip().lower()
        if install == 'y':
            install_requirements()
        else:
            print("Please install MySQL connector manually and run this script again.")
            return
    
    # Test MySQL connection
    db, config = test_mysql_connection()
    if not db:
        return
    
    # Save configuration
    if config:
        save_config(**config)
    
    # Migrate existing data
    migrate_existing_data()
    
    # Create startup script
    create_startup_script()
    
    print("\n" + "=" * 60)
    print("MySQL Setup Complete!")
    print("=" * 60)
    print("Next steps:")
    print("1. Run the application: python start_mysql_app.py")
    print("2. Or run directly: python mysql_attendance_gui.py")
    print("3. Configuration saved in: mysql_config.py")
    print("=" * 60)

if __name__ == "__main__":
    from datetime import datetime
    main()
