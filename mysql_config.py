# MySQL Configuration for Face Recognition System
# Generated on 2026-04-27 03:26:33

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "attendance_system"
MYSQL_PORT = 3306

# Use this configuration in your application
from database_core_mysql import MySQLAttendanceDatabase

db = MySQLAttendanceDatabase(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
    port=MYSQL_PORT
)
