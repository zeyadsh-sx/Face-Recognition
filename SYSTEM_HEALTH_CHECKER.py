
#!/usr/bin/env python3
"""
System Health Checker - Comprehensive Diagnostics
"""

import os
import sys
import importlib
from datetime import datetime

def check_imports():
    """Check all required imports"""
    print("🔍 Checking Imports...")
    
    required_imports = {
        'mysql.connector': 'MySQL Database Connector',
        'cv2': 'OpenCV Computer Vision',
        'numpy': 'NumPy Array Processing',
        'tkinter': 'Tkinter GUI Framework',
        'threading': 'Threading Support',
        'json': 'JSON Processing',
        'datetime': 'Date/Time Processing'
    }
    
    optional_imports = {
        'face_recognition': 'Face Recognition Library',
        'deepface': 'Deep Learning Face Analysis',
        'openpyxl': 'Excel File Processing',
        'pyautogui': 'Screenshot Capture'
    }
    
    results = {'required': {}, 'optional': {}}
    
    # Check required imports
    for module, description in required_imports.items():
        try:
            importlib.import_module(module)
            results['required'][module] = {'status': '✅ OK', 'description': description}
        except ImportError as e:
            results['required'][module] = {'status': '❌ Missing', 'description': description, 'error': str(e)}
    
    # Check optional imports
    for module, description in optional_imports.items():
        try:
            importlib.import_module(module)
            results['optional'][module] = {'status': '✅ Available', 'description': description}
        except ImportError:
            results['optional'][module] = {'status': '⚠️ Not Available', 'description': description}
    
    return results

def check_database_connection():
    """Check database connection"""
    print("🔍 Checking Database Connection...")
    
    try:
        from database_core_mysql import MySQLAttendanceDatabase
        
        db = MySQLAttendanceDatabase()
        connection_test = db.test_connection()
        
        return {
            'status': '✅ Connected' if connection_test else '❌ Failed',
            'details': 'Connection successful' if connection_test else 'Connection failed'
        }
    except Exception as e:
        return {
            'status': '❌ Error',
            'details': str(e)
        }

def check_file_structure():
    """Check required file structure"""
    print("🔍 Checking File Structure...")
    
    required_files = [
        'database_core_mysql.py',
        'gui_basic_mysql.py',
        'start_mysql_app.py',
        'mysql_config.py',
        'dashboard_final.py',
        'features_ai_advanced.py'
    ]
    
    required_directories = [
        'known_faces',
        'attendance_images',
        'unknown_faces',
        'services'
    ]
    
    results = {'files': {}, 'directories': {}}
    
    # Check files
    for file_path in required_files:
        exists = os.path.exists(file_path)
        results['files'][file_path] = {
            'status': '✅ Exists' if exists else '❌ Missing',
            'size': os.path.getsize(file_path) if exists else 0
        }
    
    # Check directories
    for dir_path in required_directories:
        exists = os.path.exists(dir_path)
        results['directories'][dir_path] = {
            'status': '✅ Exists' if exists else '❌ Missing',
            'items': len(os.listdir(dir_path)) if exists else 0
        }
    
    return results

def generate_health_report():
    """Generate comprehensive health report"""
    print("📋 Generating Health Report...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_status': 'Checking...',
        'checks': {}
    }
    
    # Run all checks
    report['checks']['imports'] = check_imports()
    report['checks']['database'] = check_database_connection()
    report['checks']['file_structure'] = check_file_structure()
    
    # Determine overall status
    overall_issues = 0
    
    # Check required imports
    for module, result in report['checks']['imports']['required'].items():
        if result['status'] == '❌ Missing':
            overall_issues += 1
    
    # Check database
    if report['checks']['database']['status'] == '❌ Error':
        overall_issues += 1
    
    # Check critical files
    critical_files = ['database_core_mysql.py', 'gui_basic_mysql.py', 'start_mysql_app.py']
    for file_path in critical_files:
        if report['checks']['file_structure']['files'].get(file_path, {}).get('status') == '❌ Missing':
            overall_issues += 1
    
    # Set overall status
    if overall_issues == 0:
        report['system_status'] = '✅ Healthy'
    elif overall_issues <= 2:
        report['system_status'] = '⚠️ Degraded'
    else:
        report['system_status'] = '❌ Unhealthy'
    
    return report

def main():
    """Main health checker function"""
    print("🚀 Starting System Health Check")
    print("=" * 60)
    
    report = generate_health_report()
    
    # Display results
    print(f"\n📊 Overall System Status: {report['system_status']}")
    print(f"🕐 Check Time: {report['timestamp']}")
    
    # Display import results
    print("\n📦 Required Imports:")
    for module, result in report['checks']['imports']['required'].items():
        print(f"   {result['status']} {module} - {result['description']}")
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    print("\n📦 Optional Imports:")
    for module, result in report['checks']['imports']['optional'].items():
        print(f"   {result['status']} {module} - {result['description']}")
    
    # Display database status
    print(f"\n🗄️ Database: {report['checks']['database']['status']}")
    print(f"   Details: {report['checks']['database']['details']}")
    
    # Display file structure
    print("\n📁 Critical Files:")
    critical_files = ['database_core_mysql.py', 'gui_basic_mysql.py', 'start_mysql_app.py']
    for file_path in critical_files:
        file_info = report['checks']['file_structure']['files'].get(file_path, {})
        print(f"   {file_info.get('status', '❌ Unknown')} {file_path}")
        if file_info.get('size', 0) > 0:
            print(f"      Size: {file_info['size']} bytes")
    
    print("\n📁 Required Directories:")
    for dir_path in ['known_faces', 'attendance_images', 'unknown_faces']:
        dir_info = report['checks']['file_structure']['directories'].get(dir_path, {})
        print(f"   {dir_info.get('status', '❌ Unknown')} {dir_path}")
        if dir_info.get('items', 0) > 0:
            print(f"      Items: {dir_info['items']}")
    
    print("\n" + "=" * 60)
    print("✅ Health Check Complete!")
    
    return report

if __name__ == "__main__":
    main()
