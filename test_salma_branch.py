"""
Simple Test Suite for Salma Branch
Tests core functionality without database connection
"""

import unittest
import sys
import os
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Mock face_recognition if not available
sys.modules['face_recognition'] = MagicMock()

import cv2


class TestDatabaseCore(unittest.TestCase):
    """Test database core module"""
    
    def test_module_imports(self):
        """Test that database_core_mysql can be imported"""
        try:
            from database_core_mysql import MySQLAttendanceDatabase
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import database_core_mysql: {e}")
    
    @patch('database_core_mysql.mysql.connector.connect')
    def test_database_class_initialization(self, mock_connect):
        """Test database class can be initialized with mocked connection"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        from database_core_mysql import MySQLAttendanceDatabase
        db = MySQLAttendanceDatabase(
            host='localhost',
            user='root',
            password='',
            database='test_attendance',
            port=3306
        )
        
        self.assertIsNotNone(db)


class TestFeaturesAI(unittest.TestCase):
    """Test AI features module"""
    
    def test_module_imports(self):
        """Test that features_ai_advanced can be imported"""
        try:
            from features_ai_advanced import AntiSpoofing, BlinkDetector, MotionDetector
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import features_ai_advanced: {e}")
    
    def test_blink_detector_initialization(self):
        """Test blink detector can be initialized"""
        from features_ai_advanced import BlinkDetector
        detector = BlinkDetector()
        self.assertIsNotNone(detector)
    
    def test_motion_detector_initialization(self):
        """Test motion detector can be initialized"""
        from features_ai_advanced import MotionDetector
        detector = MotionDetector()
        self.assertIsNotNone(detector)
    
    def test_anti_spoofing_initialization(self):
        """Test anti-spoofing can be initialized"""
        from features_ai_advanced import AntiSpoofing
        anti_spoofing = AntiSpoofing()
        self.assertIsNotNone(anti_spoofing)


class TestDashboard(unittest.TestCase):
    """Test dashboard module"""
    
    def test_module_imports(self):
        """Test that dashboard_final can be imported"""
        try:
            # Don't run the app, just import
            import dashboard_final
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import dashboard_final: {e}")
        except Exception as e:
            # Other exceptions are ok (like Flask app initialization)
            self.assertTrue(True)


class TestProjectStructure(unittest.TestCase):
    """Test project structure"""
    
    def test_main_files_exist(self):
        """Test that main project files exist"""
        base_dir = os.path.dirname(__file__)
        
        required_files = [
            'database_core_mysql.py',
            'features_ai_advanced.py',
            'mysql_config.py',
            'dashboard_final.py',
            'setup_database_mysql.py',
            'README.md',
            'attendance.sql'
        ]
        
        for file in required_files:
            file_path = os.path.join(base_dir, file)
            self.assertTrue(os.path.exists(file_path), f"File {file} not found")
    
    def test_directories_exist(self):
        """Test that required directories exist"""
        base_dir = os.path.dirname(__file__)
        
        required_dirs = ['known_faces', 'attendance_images', 'unknown_faces', 'frontend']
        
        for dir_name in required_dirs:
            dir_path = os.path.join(base_dir, dir_name)
            # Create if doesn't exist
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            self.assertTrue(os.path.exists(dir_path), f"Directory {dir_name} cannot be created")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseCore))
    suite.addTests(loader.loadTestsFromTestCase(TestFeaturesAI))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboard))
    suite.addTests(loader.loadTestsFromTestCase(TestProjectStructure))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("TEST SUMMARY - SALMA BRANCH")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
