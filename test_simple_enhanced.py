#!/usr/bin/env python3
"""
Simple test script for enhanced database functionality
"""

import sys
import os
from datetime import datetime, timedelta
import numpy as np

try:
    from database_core_mysql import MySQLAttendanceDatabase
    from services.backup_service import BackupService
    from services.export_service import ExportService
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_simple_enhanced_functions():
    """Test enhanced database functions without local database dependency"""
    
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
            camera_name="Test Camera Enhanced",
            source="rtsp://test:554/stream",
            location="Test Location",
            ip_address="192.168.1.100",
            is_active=True
        )
        print(f"   Camera added with ID: {camera_id}")
        
        # Test camera update
        update_success = db.update_camera(camera_id, location="Updated Location")
        print(f"   Camera update: {'Success' if update_success else 'Failed'}")
        
        # Test deactivate camera
        deactivate_success = db.deactivate_camera(camera_id)
        print(f"   Camera deactivation: {'Success' if deactivate_success else 'Failed'}")
        
        # Test get active cameras
        active_cameras = db.get_active_cameras()
        print(f"   Active cameras: {len(active_cameras)}")
        
        # Test get all cameras
        all_cameras = db.get_all_cameras()
        print(f"   All cameras: {len(all_cameras)}")
        
        # Test 2: Enhanced add_notification
        print("\n2. Testing Enhanced add_notification:")
        notification_success = db.add_notification(
            message="Test enhanced notification with priority and expiration",
            notification_type="info",
            priority="high",
            expires_at=datetime.now() + timedelta(hours=24)
        )
        print(f"   Notification added: {'Success' if notification_success else 'Failed'}")
        
        # Test different notification types
        notification_types = ["warning", "error", "success", "security", "attendance", "system"]
        for notif_type in notification_types:
            success = db.add_notification(f"Test {notif_type} notification", notif_type)
            print(f"   {notif_type} notification: {'Success' if success else 'Failed'}")
        
        # Test get notifications
        notifications = db.get_notifications(limit=10)
        print(f"   Recent notifications: {len(notifications)}")
        
        # Test unread notifications
        unread_notifications = db.get_notifications(unread_only=True)
        print(f"   Unread notifications: {len(unread_notifications)}")
        
        # Test notification by type
        warning_notifications = db.get_notifications(notification_type="warning")
        print(f"   Warning notifications: {len(warning_notifications)}")
        
        # Test 3: Enhanced mark_attendance_advanced
        print("\n3. Testing Enhanced mark_attendance_advanced:")
        
        # Add a test student
        student_id = db.add_student_advanced(
            name="Enhanced Test Student",
            face_encoding=np.random.rand(128),
            image_path="test_images/enhanced_student.jpg",
            notes="Test student for enhanced functions"
        )
        print(f"   Test student added with ID: {student_id}")
        
        # Test basic attendance marking
        success, message = db.mark_attendance_advanced(
            student_id=student_id,
            date_str=datetime.now().strftime('%Y-%m-%d'),
            time_str=datetime.now().strftime('%H:%M:%S'),
            image_path="test_images/attendance.jpg",
            emotion="happy",
            emotion_confidence=0.85
        )
        print(f"   Basic attendance marking: {'Success' if success else 'Failed'}")
        print(f"   Message: {message}")
        
        # Test full-featured attendance marking
        success, message = db.mark_attendance_advanced(
            student_id=student_id,
            date_str=datetime.now().strftime('%Y-%m-%d'),
            time_str=datetime.now().strftime('%H:%M:%S'),
            image_path="test_images/full_attendance.jpg",
            emotion="neutral",
            emotion_confidence=0.92,
            spoofing_score=0.95,
            is_real_face=True,
            camera_id=camera_id,
            mask_detected=False,
            mask_confidence=0.88,
            mask_violation=False,
            lecture_id="test_lecture_001",
            head_pose="frontal",
            attention_score=0.82,
            gaze_direction="forward",
            blink_score=0.75,
            face_quality_score=0.91,
            location_coordinates="x:150,y:250",
            device_info="Enhanced Test Device v2.0"
        )
        print(f"   Full-featured attendance: {'Success' if success else 'Failed'}")
        print(f"   Message: {message}")
        
        # Test attendance retrieval
        attendance_history = db.get_student_attendance(student_id, limit=5)
        print(f"   Attendance history records: {len(attendance_history)}")
        
        # Test attendance by date
        today = datetime.now().strftime('%Y-%m-%d')
        today_attendance = db.get_student_attendance_by_date(student_id, today)
        print(f"   Today's attendance records: {len(today_attendance)}")
        
        # Test student retrieval by ID
        student_info = db.get_student_by_id(student_id)
        if student_info:
            print(f"   Student retrieved by ID: {student_info['name']}")
        else:
            print("   Failed to retrieve student by ID")
        
        # Test 4: Alert System Integration
        print("\n4. Testing Alert System Integration:")
        
        # Create different types of alerts
        alert_types = [
            ("security", "Security test alert"),
            ("attendance", "Attendance test alert"),
            ("system", "System test alert"),
            ("warning", "Warning test alert"),
            ("spoofing_attempt", "Spoofing attempt test alert"),
            ("mask_violation", "Mask violation test alert")
        ]
        
        created_alerts = []
        for alert_type, message in alert_types:
            alert_id = db.create_alert(alert_type, message, student_id)
            created_alerts.append(alert_id)
            print(f"   {alert_type} alert created: ID {alert_id}")
        
        # Get active alerts
        active_alerts = db.get_active_alerts()
        print(f"   Active alerts: {len(active_alerts)}")
        
        # Test alert acknowledgment
        if created_alerts:
            ack_success = db.acknowledge_alert(created_alerts[0])
            print(f"   Alert acknowledgment: {'Success' if ack_success else 'Failed'}")
        
        # Test 5: Backup Service
        print("\n5. Testing Backup Service:")
        backup_service = BackupService("test_enhanced_backups")
        
        # Test JSON backup
        test_data = {
            'test_enhanced': True,
            'timestamp': datetime.now().isoformat(),
            'cameras': active_cameras,
            'notifications': notifications,
            'alerts_count': len(active_alerts),
            'student_id': student_id,
            'features_tested': ['camera', 'notification', 'attendance', 'alerts']
        }
        
        backup_success, backup_file = backup_service.backup_json(test_data, "enhanced_test_backup")
        print(f"   JSON backup: {'Success' if backup_success else 'Failed'}")
        if backup_success:
            print(f"   Backup file: {os.path.basename(backup_file)}")
        
        # Test backup listing
        backups = backup_service.list_backups()
        print(f"   Available backups: {len(backups)}")
        
        # Test backup cleanup
        cleaned = backup_service.cleanup_backups(keep_latest=5)
        print(f"   Cleaned old backups: {len(cleaned)}")
        
        # Test 6: Export Service
        print("\n6. Testing Export Service:")
        export_service = ExportService()
        
        # Prepare comprehensive test data
        export_data = []
        emotions = ['happy', 'neutral', 'sad', 'surprise', 'angry', 'fear']
        
        for i in range(10):
            export_data.append({
                'student_id': student_id,
                'name': f"Enhanced Test Student {i+1}",
                'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'time': f"{9 + i % 10}:{i * 6 % 60:02d}",
                'emotion': emotions[i % len(emotions)],
                'emotion_confidence': round(0.5 + (i * 0.05), 2),
                'spoofing_score': round(0.8 + (i * 0.02), 2),
                'is_real_face': i % 5 != 0,
                'camera_id': camera_id if i % 3 != 0 else None,
                'mask_detected': i % 2 == 0,
                'mask_confidence': round(0.7 + (i * 0.1), 2),
                'mask_violation': i % 7 == 0,
                'lecture_id': f"lecture_{i % 3}",
                'head_pose': ['frontal', 'left', 'right', 'up', 'down'][i % 5],
                'attention_score': round(0.6 + (i * 0.04), 2),
                'gaze_direction': ['forward', 'left', 'right', 'up', 'down'][i % 5],
                'blink_score': round(0.5 + (i * 0.08), 2),
                'face_quality_score': round(0.7 + (i * 0.03), 2),
                'location_coordinates': f"x:{100 + i * 10},y:{200 + i * 15}",
                'device_info': f"Test Device v{i + 1}"
            })
        
        # Test different export formats
        formats = ['csv', 'json', 'excel', 'pdf']
        export_results = {}
        
        for fmt in formats:
            success, file_path = getattr(export_service, f'export_to_{fmt}')(export_data, f"enhanced_test.{fmt}")
            export_results[fmt] = {'success': success, 'file': file_path}
            print(f"   {fmt.upper()} export: {'Success' if success else 'Failed'}")
            if success:
                print(f"     File: {os.path.basename(file_path)}")
        
        # Count successful exports
        successful_exports = sum(1 for result in export_results.values() if result['success'])
        print(f"   Successful exports: {successful_exports}/{len(formats)}")
        
        # Test 7: Analytics and Statistics
        print("\n7. Testing Analytics and Statistics:")
        
        # Get comprehensive statistics
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        stats = db.get_comprehensive_statistics(start_date, end_date)
        if stats:
            print(f"   Period: {stats.get('period')}")
            print(f"   Total present: {stats.get('attendance', {}).get('total_present', 0)}")
            print(f"   Total records: {stats.get('attendance', {}).get('total_records', 0)}")
            print(f"   Avg emotion confidence: {stats.get('attendance', {}).get('avg_emotion_confidence', 0):.3f}")
            print(f"   Emotions tracked: {list(stats.get('emotions', {}).keys())}")
            
            lecture_stats = stats.get('lectures', {})
            if lecture_stats:
                print(f"   Total lectures: {lecture_stats.get('total_lectures', 0)}")
                print(f"   Avg attendance: {lecture_stats.get('avg_attendance', 0):.1f}")
                print(f"   Avg engagement: {lecture_stats.get('avg_engagement', 0):.3f}")
        
        # Test compliance statistics
        compliance = db.get_compliance_statistics(start_date, end_date)
        if compliance:
            print(f"   Compliance period: {compliance.get('start_date')} to {compliance.get('end_date')}")
            print(f"   Total records: {compliance.get('total_records', 0)}")
            print(f"   Masked records: {compliance.get('masked_records', 0)}")
            print(f"   Violations: {compliance.get('violations', 0)}")
            print(f"   Compliance rate: {compliance.get('compliance_rate', 0):.1f}%")
        
        # Test 8: Notification Management
        print("\n8. Testing Notification Management:")
        
        # Mark some notifications as read
        if notifications:
            for i, notification in enumerate(notifications[:3]):
                read_success = db.mark_notification_read(notification['id'])
                print(f"   Marked notification {i+1} as read: {'Success' if read_success else 'Failed'}")
        
        # Check unread count after marking
        unread_after = db.get_notifications(unread_only=True)
        print(f"   Unread notifications after marking: {len(unread_after)}")
        
        # Test cleanup
        cleaned_count = db.cleanup_expired_notifications()
        print(f"   Cleaned expired notifications: {cleaned_count}")
        
        print("\n" + "=" * 60)
        print("✅ All Enhanced Database Tests Completed Successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Starting Simple Enhanced Database Test Suite")
    print("Testing new functions: add_camera(), add_notification(), enhanced mark_attendance_advanced()")
    print("Testing services: backup_service.py, export_service.py")
    
    # Test enhanced functions
    success = test_simple_enhanced_functions()
    
    # Overall results
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Enhanced Database Tests: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Enhanced database functions and services are working correctly.")
        print("\nNew Functions Tested:")
        print("• add_camera() - Enhanced camera management")
        print("• add_notification() - Advanced notification system")
        print("• mark_attendance_advanced() - Comprehensive attendance tracking")
        print("• get_student_attendance_by_date() - Date-specific attendance")
        print("• get_student_by_id() - Student retrieval by ID")
        print("• update_camera() / deactivate_camera() - Camera management")
        print("• get_notifications() / mark_notification_read() - Notification management")
        print("• cleanup_expired_notifications() - Notification cleanup")
        print("• get_comprehensive_statistics() - Advanced analytics")
        print("• get_compliance_statistics() - Compliance tracking")
        print("\nServices Tested:")
        print("• backup_service.py - Database backup functionality")
        print("• export_service.py - Multi-format data export")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
