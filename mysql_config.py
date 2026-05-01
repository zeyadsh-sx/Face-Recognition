# MySQL Configuration for Face Recognition System
# Generated on 2026-05-01 - Enhanced with Error Handling

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "attendance_system"
MYSQL_PORT = 3306

# Use this configuration in your application
from database_core_mysql import MySQLAttendanceDatabase

def get_database():
    """Get database connection with error handling"""
    try:
        return MySQLAttendanceDatabase(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Create database instance with error handling
try:
    db = get_database()
    if db and db.test_connection():
        print("✅ MySQL database connection successful")
    else:
        print("⚠️ MySQL database connection failed - using fallback")
except Exception as e:
    print(f"⚠️ Database initialization error: {e}")
    db = None
