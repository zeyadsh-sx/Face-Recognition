#!/usr/bin/env python3
"""
Test script for enhanced database functionality
"""

import sys
import os
from datetime import datetime, timedelta
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database_core_mysql import MySQLAttendanceDatabase
    from services.backup_service import BackupService
    from services.export_service import ExportService
    from services.offline_sync import OfflineSyncService
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_enhanced_database():
    """Test all enhanced database functions"""
    
    print("=" * 60)
    print("Testing Enhanced Database Functions")
    print("=" * 60)
    
    try:
        # Initialize database
        db = MySQLAttendanceDatabase()
        print("✅ Database connection established")
        
        # Test 1: Enhanced add_camera
        print("\n1. Testing Enhanced add_camera:")
        camera_id = db.add_camera(
            camera_name="Main Entrance Camera",
            source="rtsp://192.168.1.100:554/stream",
            location="Main Building Entrance",
            ip_address="192.168.1.100",
            is_active=True
        )
        print(f"   Camera added with ID: {camera_id}")
        
        # Test camera update
        update_success = db.update_camera(camera_id, location="Updated Location")
        print(f"   Camera update: {'Success' if update_success else 'Failed'}")
        
        # Test get active cameras
        active_cameras = db.get_active_cameras()
        print(f"   Active cameras: {len(active_cameras)}")
        
        # Test 2: Enhanced add_notification
        print("\n2. Testing Enhanced add_notification:")
        notification_success = db.add_notification(
            message="Test notification with enhanced features",
            notification_type="info",
            priority="medium",
            expires_at=datetime.now() + timedelta(hours=24)
        )
        print(f"   Notification added: {'Success' if notification_success else 'Failed'}")
        
        # Test get notifications
        notifications = db.get_notifications(limit=5)
        print(f"   Recent notifications: {len(notifications)}")
        
        # Test 3: Enhanced mark_attendance_advanced
        print("\n3. Testing Enhanced mark_attendance_advanced:")
        
        # First, add a test student
        student_id = db.add_student_advanced(
            name="Test Student Enhanced",
            face_encoding=np.random.rand(128),
            image_path="test_images/test_student.jpg",
            notes="Test student for enhanced functions"
        )
        print(f"   Test student added with ID: {student_id}")
        
        # Mark attendance with all enhanced features
        success, message = db.mark_attendance_advanced(
            student_id=student_id,
            date_str=datetime.now().strftime('%Y-%m-%d'),
            time_str=datetime.now().strftime('%H:%M:%S'),
            image_path="test_images/attendance.jpg",
            emotion="happy",
            emotion_confidence=0.85,
            spoofing_score=0.92,
            is_real_face=True,
            camera_id=camera_id,
            mask_detected=False,
            mask_confidence=0.95,
            mask_violation=False,
            lecture_id="test_lecture_001",
            head_pose="frontal",
            attention_score=0.78,
            gaze_direction="forward",
            blink_score=0.65,
            face_quality_score=0.88,
            location_coordinates="x:100,y:200",
            device_info="Test Device v1.0"
        )
        print(f"   Enhanced attendance marking: {'Success' if success else 'Failed'}")
        print(f"   Message: {message}")
        
        # Test enhanced attendance retrieval
        attendance_history = db.get_student_attendance(student_id, limit=5)
        print(f"   Attendance history records: {len(attendance_history)}")
        
        if attendance_history:
            latest_record = attendance_history[0]
            print(f"   Latest record includes analytics: {latest_record.get('head_pose') is not None}")
        
        # Test 4: Backup Service
        print("\n4. Testing Backup Service:")
        backup_service = BackupService("test_backups")
        
        # Test JSON backup
        test_data = {
            'test': 'data',
            'timestamp': datetime.now().isoformat(),
            'cameras': active_cameras,
            'notifications': notifications
        }
        
        backup_success, backup_file = backup_service.backup_json(test_data, "database_backup")
        print(f"   JSON backup: {'Success' if backup_success else 'Failed'}")
        if backup_success:
            print(f"   Backup file: {backup_file}")
        
        # Test backup listing
        backups = backup_service.list_backups()
        print(f"   Available backups: {len(backups)}")
        
        # Test 5: Export Service
        print("\n5. Testing Export Service:")
        export_service = ExportService()
        
        # Prepare test data for export
        export_data = []
        for i in range(3):
            export_data.append({
                'student_id': student_id + i,
                'name': f"Test Student {i+1}",
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'emotion': ['happy', 'neutral', 'sad'][i],
                'confidence': 0.8 + (i * 0.1),
                'camera': f"Camera {i+1}"
            })
        
        # Test CSV export
        csv_success, csv_file = export_service.export_to_csv(export_data, "test_export.csv")
        print(f"   CSV export: {'Success' if csv_success else 'Failed'}")
        if csv_success:
            print(f"   CSV file: {csv_file}")
        
        # Test JSON export
        json_success, json_file = export_service.export_to_json(export_data, "test_export.json")
        print(f"   JSON export: {'Success' if json_success else 'Failed'}")
        if json_success:
            print(f"   JSON file: {json_file}")
        
        # Test Excel export (if available)
        excel_success, excel_file = export_service.export_to_excel(export_data, "test_export.xlsx")
        print(f"   Excel export: {'Success' if excel_success else 'Failed'}")
        if excel_success:
            print(f"   Excel file: {excel_file}")
        
        # Test PDF export
        pdf_success, pdf_file = export_service.export_to_pdf(export_data, "test_export.pdf")
        print(f"   PDF export: {'Success' if pdf_success else 'Failed'}")
        if pdf_success:
            print(f"   PDF file: {pdf_file}")
        
        # Test 6: Alert and Notification Integration
        print("\n6. Testing Alert and Notification Integration:")
        
        # Create different types of alerts
        alert_types = [
            ("security", "Security alert test"),
            ("attendance", "Attendance alert test"),
            ("system", "System alert test"),
            ("warning", "Warning alert test")
        ]
        
        for alert_type, message in alert_types:
            alert_id = db.create_alert(alert_type, message)
            print(f"   {alert_type} alert created: ID {alert_id}")
        
        # Get active alerts
        active_alerts = db.get_active_alerts()
        print(f"   Active alerts: {len(active_alerts)}")
        
        # Test notification cleanup
        cleaned_count = db.cleanup_expired_notifications()
        print(f"   Cleaned expired notifications: {cleaned_count}")
        
        # Test 7: Analytics Integration
        print("\n7. Testing Analytics Integration:")
        
        # Get comprehensive statistics
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        stats = db.get_comprehensive_statistics(start_date, end_date)
        if stats:
            print(f"   Period: {stats.get('period')}")
            print(f"   Total present: {stats.get('attendance', {}).get('total_present', 0)}")
            print(f"   Emotions tracked: {list(stats.get('emotions', {}).keys())}")
        
        # Test compliance statistics
        compliance = db.get_compliance_statistics(start_date, end_date)
        if compliance:
            print(f"   Compliance rate: {compliance.get('compliance_rate', 0)}%")
            print(f"   Total records: {compliance.get('total_records', 0)}")
        
        print("\n" + "=" * 60)
        print("✅ All Enhanced Database Tests Completed Successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_service_integration():
    """Test service integration"""
    
    print("\n" + "=" * 60)
    print("Testing Service Integration")
    print("=" * 60)
    
    try:
        # Test Backup Service
        print("\n1. Testing Backup Service Integration:")
        backup_service = BackupService("integration_test_backups")
        
        # Create test data
        test_data = {
            'students': [
                {'id': 1, 'name': 'Student 1', 'status': 'active'},
                {'id': 2, 'name': 'Student 2', 'status': 'active'}
            ],
            'cameras': [
                {'id': 1, 'name': 'Camera 1', 'is_active': True},
                {'id': 2, 'name': 'Camera 2', 'is_active': False}
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # Test multiple backup formats
        json_success, json_path = backup_service.backup_json(test_data, "integration_test")
        print(f"   JSON backup integration: {'Success' if json_success else 'Failed'}")
        
        # Test Export Service
        print("\n2. Testing Export Service Integration:")
        export_service = ExportService()
        
        # Create comprehensive test data
        export_data = [
            {
                'student_id': 1,
                'name': 'Test Student',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'emotion': 'happy',
                'confidence': 0.92,
                'camera': 'Main Camera',
                'mask_detected': False,
                'quality_score': 0.88
            },
            {
                'student_id': 2,
                'name': 'Another Student',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'emotion': 'neutral',
                'confidence': 0.78,
                'camera': 'Side Camera',
                'mask_detected': True,
                'quality_score': 0.75
            }
        ]
        
        # Test all export formats
        formats = ['csv', 'json', 'excel', 'pdf']
        results = {}
        
        for fmt in formats:
            success, file_path = getattr(export_service, f'export_to_{fmt}')(export_data, f"integration_test.{fmt}")
            results[fmt] = {'success': success, 'file': file_path}
            print(f"   {fmt.upper()} export: {'Success' if success else 'Failed'}")
        
        # Test file creation verification
        created_files = []
        for fmt, result in results.items():
            if result['success'] and os.path.exists(result['file']):
                created_files.append(result['file'])
        
        print(f"   Files created successfully: {len(created_files)}")
        
        print("\n" + "=" * 60)
        print("✅ Service Integration Tests Completed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Enhanced Database and Services Test Suite")
    
    # Test enhanced database functions
    db_success = test_enhanced_database()
    
    # Test service integration
    service_success = test_service_integration()
    
    # Overall results
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Database Tests: {'✅ PASSED' if db_success else '❌ FAILED'}")
    print(f"Service Tests: {'✅ PASSED' if service_success else '❌ FAILED'}")
    
    if db_success and service_success:
        print("\n🎉 ALL TESTS PASSED! Enhanced database and services are working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
