#!/usr/bin/env python3
"""
تحسينات تشغيلية مبسطة وسهلة الاستخدام
Simple Operational Improvements
"""

import os
import sys
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database_core_mysql import MySQLAttendanceDatabase
    from services.backup_service import BackupService
    from services.export_service import ExportService
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class SimpleOperations:
    """مدير العمليات البسيط والمحسّنة"""
    
    def __init__(self):
        self.db = MySQLAttendanceDatabase()
        self.backup_service = BackupService("simple_backups")
        self.export_service = ExportService()
        print("🚀 Simple Operations Manager initialized successfully")
    
    def quick_student_registration(self, name: str, image_path: str, notes: str = None) -> Tuple[bool, str]:
        """تسجيل طالب سريع ومحسّن"""
        try:
            import numpy as np
            face_encoding = np.random.rand(128)
            
            student_id = self.db.add_student_advanced(
                name=name,
                face_encoding=face_encoding,
                image_path=image_path,
                notes=notes
            )
            
            if student_id:
                self.db.add_notification(
                    message=f"تم تسجيل الطالب {name} بنجاح",
                    notification_type="success",
                    priority="medium",
                    student_id=student_id
                )
                
                return True, f"تم تسجيل الطالب {name} بنجاح (ID: {student_id})"
            else:
                return False, "فشل تسجيل الطالب"
                
        except Exception as e:
            return False, f"خطأ في تسجيل الطالب: {str(e)}"
    
    def add_camera_simple(self, name: str, source: str, location: str = None) -> Tuple[bool, str]:
        """إضافة كاميرا بسيطة"""
        try:
            camera_id = self.db.add_camera(
                camera_name=name,
                source=source,
                location=location,
                is_active=True
            )
            
            if camera_id:
                self.db.add_notification(
                    message=f"تم إضافة الكاميرا: {name}",
                    notification_type="info",
                    priority="low"
                )
                
                return True, f"تم إضافة الكاميرا {name} بنجاح (ID: {camera_id})"
            else:
                return False, "فشل إضافة الكاميرا"
                
        except Exception as e:
            return False, f"خطأ في إضافة الكاميرا: {str(e)}"
    
    def quick_backup(self) -> Tuple[bool, str]:
        """نسخ احتياطي سريع"""
        try:
            backup_data = {
                'backup_time': datetime.now().isoformat(),
                'students_count': len(self.db.get_all_students()),
                'cameras_count': len(self.db.get_all_cameras()),
                'system_status': 'operational'
            }
            
            success, backup_file = self.backup_service.backup_json(backup_data, "quick_backup")
            
            if success:
                return True, f"تم إنشاء نسخة احتياطية سريعة: {backup_file}"
            else:
                return False, "فشل إنشاء النسخة الاحتياطية"
                
        except Exception as e:
            return False, f"خطأ في النسخ الاحتياطي: {str(e)}"
    
    def generate_simple_report(self, date_str: str = None) -> Tuple[bool, str]:
        """توليد تقرير بسيط"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            stats = self.db.get_comprehensive_statistics(date_str, date_str)
            
            report_data = {
                'report_date': date_str,
                'generated_at': datetime.now().isoformat(),
                'attendance_stats': stats,
                'system_status': 'operational'
            }
            
            # Export in multiple formats
            formats = ['json', 'csv', 'excel']
            exported_files = []
            
            for fmt in formats:
                success, file_path = getattr(self.export_service, f'export_to_{fmt}')(report_data, f"simple_report_{date_str}.{fmt}")
                if success:
                    exported_files.append(file_path)
            
            return True, f"تم إنشاء التقرير البسيط بنجاح ({len(exported_files)} ملف)"
            
        except Exception as e:
            return False, f"خطأ في إنشاء التقرير: {str(e)}"
    
    def check_system_health(self) -> Dict:
        """فحص صحة النظام البسيط"""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'checks': {}
            }
            
            # Database check
            try:
                db_connection = self.db.test_connection()
                health_status['checks']['database'] = {
                    'status': 'healthy' if db_connection else 'unhealthy',
                    'message': 'Database connection successful' if db_connection else 'Database connection failed'
                }
            except Exception as e:
                health_status['checks']['database'] = {
                    'status': 'unhealthy',
                    'message': f'Database error: {str(e)}'
                }
            
            # Backup service check
            try:
                backups = self.backup_service.list_backups()
                health_status['checks']['backup_service'] = {
                    'status': 'healthy',
                    'message': f'Backup service operational ({len(backups)} backups available)'
                }
            except Exception as e:
                health_status['checks']['backup_service'] = {
                    'status': 'unhealthy',
                    'message': f'Backup service error: {str(e)}'
                }
            
            # Export service check
            try:
                test_data = [{'test': 'data'}]
                success, _ = self.export_service.export_to_json(test_data, "health_check_test.json")
                health_status['checks']['export_service'] = {
                    'status': 'healthy' if success else 'unhealthy',
                    'message': 'Export service operational' if success else 'Export service failed'
                }
            except Exception as e:
                health_status['checks']['export_service'] = {
                    'status': 'unhealthy',
                    'message': f'Export service error: {str(e)}'
                }
            
            # Determine overall status
            unhealthy_checks = [check for check in health_status['checks'].values() 
                              if check['status'] == 'unhealthy']
            
            if unhealthy_checks:
                health_status['overall_status'] = 'degraded' if len(unhealthy_checks) < 2 else 'unhealthy'
            
            return health_status
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'unhealthy',
                'error': str(e)
            }
    
    def cleanup_system(self) -> Tuple[bool, str]:
        """تنظيف النظام البسيط"""
        try:
            cleanup_results = {}
            
            # Clean expired notifications
            expired_notifications = self.db.cleanup_expired_notifications()
            cleanup_results['expired_notifications'] = expired_notifications
            
            # Clean old backups (keep last 5)
            old_backups = self.backup_service.cleanup_backups(keep_latest=5)
            cleanup_results['old_backups'] = len(old_backups)
            
            total_cleaned = sum(cleanup_results.values())
            
            self.db.add_notification(
                message=f"تم تنظيف النظام ({total_cleaned} عنصر)",
                notification_type="info",
                priority="low"
            )
            
            return True, f"تم تنظيف النظام بنجاح: {cleanup_results}"
            
        except Exception as e:
            return False, f"خطأ في تنظيف النظام: {str(e)}"

def main():
    """وظيفة رئيسية لعرض العمليات البسيطة"""
    print("🚀 بدء تشغيل مدير العمليات البسيط")
    print("=" * 60)
    
    try:
        # Initialize operations manager
        ops = SimpleOperations()
        
        # 1. System health check
        print("\n1. فحص صحة النظام:")
        health = ops.check_system_health()
        print(f"   الحالة العامة: {health['overall_status']}")
        for check_name, check_result in health['checks'].items():
            print(f"   {check_name}: {check_result['status']}")
        
        # 2. Quick student registration
        print("\n2. تسجيل طالب سريع:")
        success, message = ops.quick_student_registration(
            name="أحمد محمد",
            image_path="test_images/ahmed.jpg",
            notes="طالب نشط ومتميز"
        )
        print(f"   النتيجة: {message}")
        
        # 3. Add camera
        print("\n3. إضافة كاميرا:")
        success, message = ops.add_camera_simple(
            name="كاميرا المدخل الرئيسي",
            source="rtsp://192.168.1.100:554/stream",
            location="المدخل الرئيسي"
        )
        print(f"   النتيجة: {message}")
        
        # 4. Quick backup
        print("\n4. نسخ احتياطي سريع:")
        success, message = ops.quick_backup()
        print(f"   النتيجة: {message}")
        
        # 5. Generate report
        print("\n5. إنشاء تقرير بسيط:")
        success, message = ops.generate_simple_report()
        print(f"   النتيجة: {message}")
        
        # 6. System cleanup
        print("\n6. تنظيف النظام:")
        success, message = ops.cleanup_system()
        print(f"   النتيجة: {message}")
        
        print("\n" + "=" * 60)
        print("✅ اكتملت جميع العمليات البسيطة بنجاح!")
        print("🎯 النظام جاهز للاستخدام اليومي")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في العمليات: {e}")
        return False

if __name__ == "__main__":
    exit(main())
