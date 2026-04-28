import mysql.connector
from mysql.connector import Error
import json
import pickle
from datetime import datetime, date, timedelta
import os
from typing import Optional, List, Dict, Any

class MySQLAttendanceDatabase:
    """MySQL database implementation for advanced attendance system"""
    
    def __init__(self, host='localhost', database='attendance_system', 
                 user='root', password='', port=3306):
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'autocommit': True,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.connection_params)
        except Error as e:
            print(f"Database connection error: {e}")
            raise
    
    def init_database(self):
        """Initialize MySQL database and tables"""
        try:
            # Connect without database first to create it
            temp_params = self.connection_params.copy()
            db_name = temp_params.pop('database')
            
            conn = mysql.connector.connect(**temp_params)
            cursor = conn.cursor()
            
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {db_name}")
            
            # Create tables
            self._create_students_table(cursor)
            self._create_cameras_table(cursor)
            self._create_attendance_table(cursor)
            self._create_face_data_table(cursor)
            self._create_unknown_faces_table(cursor)
            self._create_lecture_sessions_table(cursor)
            self._create_lecture_attendance_table(cursor)
            self._ensure_attendance_schema(cursor)
            self._ensure_lecture_attendance_schema(cursor)
            self._create_attendance_alerts_table(cursor)
            self._create_emotion_analytics_table(cursor)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("MySQL database initialized successfully!")
            
        except Error as e:
            print(f"Database initialization error: {e}")
            raise
    
    def _create_students_table(self, cursor):
        """Create students table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                face_encoding LONGBLOB,
                image_path VARCHAR(500),
                status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    def _create_attendance_table(self, cursor):
        """Create enhanced attendance table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                image_path VARCHAR(500),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                emotion VARCHAR(50),
                emotion_confidence DECIMAL(5,4),
                spoofing_score DECIMAL(5,4),
                is_real_face BOOLEAN DEFAULT TRUE,
                camera_id INT DEFAULT NULL,
                mask_detected BOOLEAN DEFAULT NULL,
                mask_confidence DECIMAL(5,4) DEFAULT NULL,
                mask_violation BOOLEAN DEFAULT FALSE,
                lecture_id VARCHAR(100),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE SET NULL,
                UNIQUE KEY unique_student_date (student_id, date),
                INDEX idx_date (date),
                INDEX idx_student_id (student_id),
                INDEX idx_camera_id (camera_id),
                INDEX idx_lecture_id (lecture_id),
                INDEX idx_emotion (emotion),
                INDEX idx_mask_violation (mask_violation)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    def _create_face_data_table(self, cursor):
        """Create face data table for multiple encodings"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                face_encoding LONGBLOB NOT NULL,
                image_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_primary BOOLEAN DEFAULT FALSE,
                quality_score DECIMAL(5,4) DEFAULT 0.8000,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                INDEX idx_student_id (student_id),
                INDEX idx_is_primary (is_primary)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

    def _create_cameras_table(self, cursor):
        """Create cameras table for multi-camera support"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cameras (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                source VARCHAR(500) NOT NULL,
                location VARCHAR(255) DEFAULT NULL,
                ip_address VARCHAR(255) DEFAULT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_camera_source (source),
                INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    def _create_unknown_faces_table(self, cursor):
        """Create unknown faces table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unknown_faces (
                id INT AUTO_INCREMENT PRIMARY KEY,
                image_path VARCHAR(500) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                face_encoding LONGBLOB,
                processed BOOLEAN DEFAULT FALSE,
                notes TEXT,
                INDEX idx_timestamp (timestamp),
                INDEX idx_processed (processed)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    def _create_lecture_sessions_table(self, cursor):
        """Create lecture sessions table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_sessions (
                id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                course_code VARCHAR(50),
                instructor VARCHAR(255),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NULL,
                total_attendees INT DEFAULT 0,
                engagement_score DECIMAL(5,4) DEFAULT 0.0000,
                emotions_summary JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_start_time (start_time),
                INDEX idx_course_code (course_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    def _create_lecture_attendance_table(self, cursor):
        """Create lecture attendance table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lecture_id VARCHAR(100) NOT NULL,
                student_id INT,
                entry_time TIME NOT NULL,
                exit_time TIME NULL,
                duration_seconds INT DEFAULT 0,
                duration VARCHAR(50) DEFAULT NULL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                emotion VARCHAR(50),
                emotion_confidence DECIMAL(5,4),
                head_pose VARCHAR(255),
                attention_score DECIMAL(5,4),
                gaze_direction VARCHAR(50),
                blink_score DECIMAL(5,4),
                camera_id INT DEFAULT NULL,
                mask_detected BOOLEAN DEFAULT NULL,
                mask_confidence DECIMAL(5,4) DEFAULT NULL,
                mask_violation BOOLEAN DEFAULT FALSE,
                status ENUM('present','left') DEFAULT 'present',
                FOREIGN KEY (lecture_id) REFERENCES lecture_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE SET NULL,
                INDEX idx_lecture_id (lecture_id),
                INDEX idx_student_id (student_id),
                INDEX idx_status (status),
                INDEX idx_camera_id (camera_id),
                INDEX idx_mask_violation (mask_violation)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

    def _ensure_lecture_attendance_schema(self, cursor):
        """Ensure lecture attendance table contains new presence tracking columns"""
        try:
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'entry_time'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN entry_time TIME NOT NULL AFTER student_id")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'exit_time'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN exit_time TIME NULL AFTER entry_time")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'duration_seconds'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN duration_seconds INT DEFAULT 0 AFTER exit_time")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'duration'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN duration VARCHAR(50) DEFAULT NULL AFTER duration_seconds")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'last_seen'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER duration")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'status'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN status ENUM('present','left') DEFAULT 'present' AFTER emotion_confidence")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'head_pose'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN head_pose VARCHAR(255) DEFAULT NULL AFTER emotion_confidence")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'attention_score'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN attention_score DECIMAL(5,4) DEFAULT NULL AFTER head_pose")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'gaze_direction'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN gaze_direction VARCHAR(50) DEFAULT NULL AFTER attention_score")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'blink_score'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN blink_score DECIMAL(5,4) DEFAULT NULL AFTER gaze_direction")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'camera_id'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN camera_id INT DEFAULT NULL AFTER blink_score")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'mask_detected'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN mask_detected BOOLEAN DEFAULT NULL AFTER camera_id")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'mask_confidence'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN mask_confidence DECIMAL(5,4) DEFAULT NULL AFTER mask_detected")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'mask_violation'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD COLUMN mask_violation BOOLEAN DEFAULT FALSE AFTER mask_confidence")
            cursor.execute("SHOW COLUMNS FROM lecture_attendance LIKE 'camera_id'")
            if cursor.fetchone():
                cursor.execute("ALTER TABLE lecture_attendance ADD INDEX idx_camera_id (camera_id)")
        except Error as e:
            print(f"Error ensuring lecture attendance schema: {e}")

    def _ensure_attendance_schema(self, cursor):
        """Ensure attendance table has camera tracking columns"""
        try:
            cursor.execute("SHOW COLUMNS FROM attendance LIKE 'camera_id'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE attendance ADD COLUMN camera_id INT DEFAULT NULL AFTER is_real_face")
            cursor.execute("SHOW COLUMNS FROM attendance LIKE 'camera_id'")
            if cursor.fetchone():
                cursor.execute("ALTER TABLE attendance ADD INDEX idx_camera_id (camera_id)")
        except Error as e:
            print(f"Error ensuring attendance schema: {e}")

    def _create_attendance_alerts_table(self, cursor):
        """Create attendance alerts table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                alert_type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                student_id INT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL,
                INDEX idx_timestamp (timestamp),
                INDEX idx_alert_type (alert_type),
                INDEX idx_acknowledged (acknowledged)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    def _create_emotion_analytics_table(self, cursor):
        """Create emotion analytics table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_analytics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                date DATE NOT NULL,
                time TIME NOT NULL,
                emotion VARCHAR(50) NOT NULL,
                confidence DECIMAL(5,4),
                context VARCHAR(100),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                INDEX idx_student_id (student_id),
                INDEX idx_date (date),
                INDEX idx_emotion (emotion)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    # Student management methods
    def add_student_advanced(self, name: str, face_encoding: Any, image_path: Optional[str] = None, 
                           notes: Optional[str] = None) -> Optional[int]:
        """Add student with enhanced features"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                encoding_blob = pickle.dumps(face_encoding)
                
                # Insert or update student
                cursor.execute('''
                    INSERT INTO students (name, face_encoding, image_path, notes)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    face_encoding = VALUES(face_encoding),
                    image_path = VALUES(image_path),
                    notes = VALUES(notes),
                    updated_at = CURRENT_TIMESTAMP
                ''', (name, encoding_blob, image_path, notes))
                
                # Get student ID
                cursor.execute('SELECT id FROM students WHERE name = %s', (name,))
                student_id = cursor.fetchone()[0]
                
                # Add to face_data table as primary encoding
                cursor.execute('''
                    INSERT INTO face_data (student_id, face_encoding, image_path, is_primary, quality_score)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (student_id, encoding_blob, image_path, True, 0.8))
                
                return student_id
                
        except Error as e:
            print(f"Error adding student: {e}")
            return None

    def add_student(self, name: str, face_encoding: Any, image_path: Optional[str] = None, 
                    notes: Optional[str] = None) -> Optional[int]:
        """Backwards-compatible add_student alias"""
        return self.add_student_advanced(name, face_encoding, image_path, notes)
    
    def get_all_students(self) -> List[Dict]:
        """Get all students with their face encodings"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, name, face_encoding, image_path, status, notes, created_at, updated_at
                    FROM students 
                    WHERE status = 'active'
                    ORDER BY name
                ''')
                
                students = []
                for row in cursor.fetchall():
                    students.append({
                        'id': row['id'],
                        'name': row['name'],
                        'face_encoding': pickle.loads(row['face_encoding']) if row['face_encoding'] else None,
                        'image_path': row['image_path'],
                        'status': row['status'],
                        'notes': row['notes'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return students
                
        except Error as e:
            print(f"Error getting students: {e}")
            return []
    
    def get_student_by_name(self, name: str) -> Optional[Dict]:
        """Get student by name with full details"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, name, face_encoding, image_path, status, notes, created_at, updated_at
                    FROM students 
                    WHERE name = %s AND status = 'active'
                ''', (name,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'face_encoding': pickle.loads(row['face_encoding']) if row['face_encoding'] else None,
                        'image_path': row['image_path'],
                        'status': row['status'],
                        'notes': row['notes'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                return None
                
        except Error as e:
            print(f"Error getting student by name: {e}")
            return None
    
    def update_student_status(self, student_id: int, status: str, notes: Optional[str] = None) -> bool:
        """Update student status and notes"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE students 
                    SET status = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (status, notes, student_id))
                return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating student status: {e}")
            return False
    
    # Attendance methods
    def mark_attendance_advanced(self, student_id: int, date_str: str, time_str: str, 
                                image_path: Optional[str] = None, emotion: Optional[str] = None,
                                emotion_confidence: Optional[float] = None, 
                                spoofing_score: Optional[float] = None,
                                is_real_face: Optional[bool] = None, 
                                camera_id: Optional[int] = None,
                                mask_detected: Optional[bool] = None,
                                mask_confidence: Optional[float] = None,
                                mask_violation: Optional[bool] = False,
                                lecture_id: Optional[str] = None) -> tuple[bool, str]:
        """Mark attendance with advanced validation, anti-spoofing, and alerts"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # ================= VALIDATION =================
                if not student_id:
                    return False, "Invalid student ID"

                if not date_str or not time_str:
                    return False, "Date and time are required"

                # ================= CHECK STUDENT EXISTS =================
                cursor.execute("SELECT id, status FROM students WHERE id = %s", (student_id,))
                student = cursor.fetchone()

                if not student:
                    return False, "Student not found"

                if student[1] != 'active':
                    return False, f"Student is not active (status: {student[1]})"

                # ================= DUPLICATE CHECK =================
                cursor.execute('''
                    SELECT id FROM attendance 
                    WHERE student_id = %s AND date = %s
                ''', (student_id, date_str))

                if cursor.fetchone():
                    return False, f"Attendance already marked for {date_str}"

                # ================= ANTI-SPOOFING CHECK =================
                if is_real_face is False:
                    self.create_alert(
                        "spoofing_attempt",
                        f"Spoofing attempt detected for student ID {student_id}",
                        student_id
                    )
                    return False, "Fake face detected (spoofing)"

                if mask_violation:
                    self.create_alert(
                        "mask_violation",
                        f"Mask violation detected for student ID {student_id}",
                        student_id
                    )

                # ================= INSERT ATTENDANCE =================
                cursor.execute('''
                    INSERT INTO attendance 
                    (student_id, date, time, image_path, emotion, emotion_confidence, 
                     spoofing_score, is_real_face, camera_id, mask_detected, mask_confidence, mask_violation, lecture_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    student_id, date_str, time_str, image_path,
                    emotion, emotion_confidence,
                    spoofing_score, is_real_face, camera_id,
                    mask_detected, mask_confidence, mask_violation, lecture_id
                ))

                cursor.execute('''
                    INSERT INTO emotion_analytics 
                    (student_id, date, time, emotion, confidence, context)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    student_id, date_str, time_str,
                    emotion, emotion_confidence, 'attendance'
                ))

                # ================= LATE DETECTION =================
                try:
                    hour = int(time_str.split(':')[0])
                    if hour >= 10:
                        self.create_alert(
                            "late_attendance",
                            f"Student ID {student_id} arrived late at {time_str}",
                            student_id
                        )
                except:
                    pass

                # ================= LOW CONFIDENCE ALERT =================
                if emotion_confidence is not None and emotion_confidence < 0.4:
                    self.create_alert(
                        "low_confidence",
                        f"Low emotion confidence detected for student ID {student_id}",
                        student_id
                    )

                # ================= LOW SPOOF SCORE ALERT =================
                if spoofing_score is not None and spoofing_score < 0.3:
                    self.create_alert(
                        "suspicious_activity",
                        f"Low spoofing score for student ID {student_id}",
                        student_id
                    )

                return True, "Attendance marked successfully (advanced)"

        except Error as e:
            print(f"Error marking attendance: {e}")
            return False, f"Database error: {e}"

    def create_or_update_lecture_presence(self, lecture_id: str, student_id: int, 
                                          entry_time: datetime.time, emotion: Optional[str] = None,
                                          emotion_confidence: Optional[float] = None,
                                          head_pose: Optional[str] = None,
                                          attention_score: Optional[float] = None,
                                          gaze_direction: Optional[str] = None,
                                          blink_score: Optional[float] = None,
                                          camera_id: Optional[int] = None,
                                          mask_detected: Optional[bool] = None,
                                          mask_confidence: Optional[float] = None,
                                          mask_violation: Optional[bool] = False) -> Optional[int]:
        """Create or update an open lecture presence record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM lecture_attendance
                    WHERE lecture_id = %s AND student_id = %s AND status = 'present'
                    ORDER BY id DESC
                    LIMIT 1
                ''', (lecture_id, student_id))
                row = cursor.fetchone()

                if row:
                    attendance_id = row[0]
                    cursor.execute('''
                        UPDATE lecture_attendance
                        SET last_seen = %s, emotion = %s, emotion_confidence = %s,
                            head_pose = %s, attention_score = %s, gaze_direction = %s,
                            blink_score = %s, camera_id = %s, mask_detected = %s,
                            mask_confidence = %s, mask_violation = %s
                        WHERE id = %s
                    ''', (
                        datetime.now(), emotion, emotion_confidence,
                        head_pose, attention_score, gaze_direction,
                        blink_score, camera_id, mask_detected, mask_confidence,
                        mask_violation, attendance_id
                    ))
                    if mask_violation:
                        self.create_alert(
                            "mask_violation",
                            f"Mask violation detected for student ID {student_id} in lecture {lecture_id}",
                            student_id
                        )
                    if attention_score is not None and attention_score < 0.45:
                        self.create_alert(
                            "inattention_alert",
                            f"Low attention detected for student ID {student_id} in lecture {lecture_id}",
                            student_id
                        )
                    return attendance_id

                cursor.execute('''
                    INSERT INTO lecture_attendance
                    (lecture_id, student_id, entry_time, last_seen, emotion, emotion_confidence,
                     head_pose, attention_score, gaze_direction, blink_score, camera_id,
                     mask_detected, mask_confidence, mask_violation, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'present')
                ''', (
                    lecture_id, student_id, entry_time, datetime.now(), emotion, emotion_confidence,
                    head_pose, attention_score, gaze_direction, blink_score, camera_id,
                    mask_detected, mask_confidence, mask_violation
                ))
                attendance_id = cursor.lastrowid
                if mask_violation:
                    self.create_alert(
                        "mask_violation",
                        f"Mask violation detected for student ID {student_id} in lecture {lecture_id}",
                        student_id
                    )
                if attention_score is not None and attention_score < 0.45:
                    self.create_alert(
                        "inattention_alert",
                        f"Low attention detected for student ID {student_id} in lecture {lecture_id}",
                        student_id
                    )
                self.update_lecture_session_attendance(lecture_id)
                return attendance_id

        except Error as e:
            print(f"Error creating/updating lecture presence: {e}")
            return None

    def close_lecture_presence(self, lecture_id: str, student_id: int, exit_time: datetime.time) -> bool:
        """Close a student's lecture presence and compute duration"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, entry_time
                    FROM lecture_attendance
                    WHERE lecture_id = %s AND student_id = %s AND status = 'present'
                    ORDER BY id DESC
                    LIMIT 1
                ''', (lecture_id, student_id))
                row = cursor.fetchone()

                if not row:
                    return False

                attendance_id = row['id']
                entry_time = row['entry_time']
                if isinstance(entry_time, str):
                    entry_time = datetime.strptime(entry_time, '%H:%M:%S').time()
                seconds = int(
                    (datetime.combine(datetime.today(), exit_time) - 
                     datetime.combine(datetime.today(), entry_time)).total_seconds()
                )
                duration = str(timedelta(seconds=max(seconds, 0)))

                cursor.execute('''
                    UPDATE lecture_attendance
                    SET exit_time = %s,
                        duration_seconds = %s,
                        duration = %s,
                        status = 'left',
                        last_seen = %s
                    WHERE id = %s
                ''', (exit_time, seconds, duration, datetime.now(), attendance_id))

                self.update_lecture_session_attendance(lecture_id)
                return True

        except Error as e:
            print(f"Error closing lecture presence: {e}")
            return False

    def update_lecture_session_attendance(self, lecture_id: str) -> bool:
        """Update total attendee count for a lecture session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE lecture_sessions
                    SET total_attendees = (
                        SELECT COUNT(DISTINCT student_id)
                        FROM lecture_attendance
                        WHERE lecture_id = %s
                    )
                    WHERE id = %s
                ''', (lecture_id, lecture_id))
                return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating lecture session attendance count: {e}")
            return False

    def get_lecture_presence(self, lecture_id: str) -> List[Dict]:
        """Get detailed presence records for a lecture session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT la.id, la.lecture_id, la.student_id, s.name AS student_name,
                           la.entry_time, la.exit_time, la.duration_seconds, la.duration,
                           la.status, la.last_seen, la.emotion, la.emotion_confidence,
                           la.head_pose, la.attention_score, la.gaze_direction, la.blink_score,
                           la.mask_detected, la.mask_confidence, la.mask_violation
                    FROM lecture_attendance la
                    LEFT JOIN students s ON la.student_id = s.id
                    WHERE la.lecture_id = %s
                    ORDER BY la.entry_time, la.student_id
                ''', (lecture_id,))
                return list(cursor.fetchall())
        except Error as e:
            print(f"Error fetching lecture presence records: {e}")
            return []

    def mark_attendance(self, student_id: int, date_str: str, time_str: str,
                              image_path: Optional[str] = None, emotion: Optional[str] = None,
                              emotion_confidence: Optional[float] = None, 
                              spoofing_score: Optional[float] = None,
                              is_real_face: Optional[bool] = None,
                              mask_detected: Optional[bool] = None,
                              mask_confidence: Optional[float] = None,
                              mask_violation: Optional[bool] = False,
                              lecture_id: Optional[str] = None) -> tuple[bool, str]:
        """Mark attendance with advanced features"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if attendance already exists
                cursor.execute('''
                    SELECT id FROM attendance 
                    WHERE student_id = %s AND date = %s
                ''', (student_id, date_str))
                
                if cursor.fetchone():
                    return False, f"Attendance already marked for {date_str}"
                
                if mask_violation:
                    self.create_alert(
                        "mask_violation",
                        f"Mask violation detected for student ID {student_id}",
                        student_id
                    )
                
                # Insert attendance record
                cursor.execute('''
                    INSERT INTO attendance 
                    (student_id, date, time, image_path, emotion, emotion_confidence, 
                     spoofing_score, is_real_face, mask_detected, mask_confidence, mask_violation, lecture_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (student_id, date_str, time_str, image_path, emotion, 
                       emotion_confidence, spoofing_score, is_real_face,
                       mask_detected, mask_confidence, mask_violation, lecture_id))
                
                # Record emotion analytics if available
                if emotion:
                    cursor.execute('''
                        INSERT INTO emotion_analytics 
                        (student_id, date, time, emotion, confidence, context)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (student_id, date_str, time_str, emotion, emotion_confidence, 'attendance'))
                
                return True, "Attendance marked successfully"
                
        except Error as e:
            print(f"Error marking attendance: {e}")
            return False, f"Error marking attendance: {e}"
    
    def get_attendance_with_emotions(self, date_str: str) -> List[Dict]:
        """Get attendance with emotion and mask data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT s.name, a.time, a.image_path, a.timestamp, a.emotion, 
                           a.emotion_confidence, a.spoofing_score, a.is_real_face,
                           a.camera_id, a.mask_detected, a.mask_confidence, a.mask_violation
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.date = %s
                    ORDER BY a.time
                ''', (date_str,))
                
                return list(cursor.fetchall())
                
        except Error as e:
            print(f"Error getting attendance with emotions: {e}")
            return []
    
    def get_attendance_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get attendance records for a date range"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT s.name, a.date, a.time, a.image_path, a.timestamp, a.emotion,
                           a.mask_detected, a.mask_confidence, a.mask_violation
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.date BETWEEN %s AND %s
                    ORDER BY a.date, a.time
                ''', (start_date, end_date))
                
                return list(cursor.fetchall())
                
        except Error as e:
            print(f"Error getting attendance by date range: {e}")
            return []
    
    # Unknown faces methods
    def add_unknown_face(self, image_path: str, face_encoding: Optional[Any] = None, 
                        notes: Optional[str] = None) -> Optional[int]:
        """Add unknown face record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                encoding_blob = pickle.dumps(face_encoding) if face_encoding else None
                
                cursor.execute('''
                    INSERT INTO unknown_faces (image_path, face_encoding, notes)
                    VALUES (%s, %s, %s)
                ''', (image_path, encoding_blob, notes))
                
                return cursor.lastrowid
                
        except Error as e:
            print(f"Error adding unknown face: {e}")
            return None
    
    def get_unknown_faces(self, limit: int = 20) -> List[Dict]:
        """Get recent unknown faces"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, image_path, timestamp, processed, notes
                    FROM unknown_faces
                    ORDER BY timestamp DESC
                    LIMIT %s
                ''', (limit,))
                
                return list(cursor.fetchall())
                
        except Error as e:
            print(f"Error getting unknown faces: {e}")
            return []
    
    # Lecture methods
    def create_lecture_session(self, lecture_id: str, name: str, course_code: str, instructor: str) -> bool:
        """Create new lecture session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO lecture_sessions (id, name, course_code, instructor, start_time)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (lecture_id, name, course_code, instructor, datetime.now()))
                
                return True
                
        except Error as e:
            print(f"Error creating lecture session: {e}")
            return False
    
    def end_lecture_session(self, lecture_id: str, engagement_score: Optional[float] = None, 
                           emotions_summary: Optional[Dict] = None) -> bool:
        """End lecture session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                emotions_json = json.dumps(emotions_summary) if emotions_summary else None
                
                cursor.execute('''
                    UPDATE lecture_sessions 
                    SET end_time = %s, engagement_score = %s, emotions_summary = %s
                    WHERE id = %s
                ''', (datetime.now(), engagement_score, emotions_json, lecture_id))
                
                return cursor.rowcount > 0
                
        except Error as e:
            print(f"Error ending lecture session: {e}")
            return False
    
    def get_lecture_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent lecture sessions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, name, course_code, instructor, start_time, end_time, 
                           total_attendees, engagement_score, emotions_summary
                    FROM lecture_sessions
                    ORDER BY start_time DESC
                    LIMIT %s
                ''', (limit,))
                
                sessions = []
                for row in cursor.fetchall():
                    emotions_summary = json.loads(row['emotions_summary']) if row['emotions_summary'] else {}
                    sessions.append({
                        'id': row['id'],
                        'name': row['name'],
                        'course_code': row['course_code'],
                        'instructor': row['instructor'],
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'total_attendees': row['total_attendees'],
                        'engagement_score': row['engagement_score'],
                        'emotions_summary': emotions_summary
                    })
                
                return sessions
                
        except Error as e:
            print(f"Error getting lecture sessions: {e}")
            return []
    
    # Alert methods
    def create_alert(self, alert_type: str, message: str, student_id: Optional[int] = None) -> Optional[int]:
        """Create attendance alert"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO attendance_alerts (alert_type, message, student_id)
                    VALUES (%s, %s, %s)
                ''', (alert_type, message, student_id))
                
                return cursor.lastrowid
                
        except Error as e:
            print(f"Error creating alert: {e}")
            return None
    
    def get_active_alerts(self) -> List[Dict]:
        """Get unacknowledged alerts"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT aa.id, aa.alert_type, aa.message, aa.timestamp, s.name
                    FROM attendance_alerts aa
                    LEFT JOIN students s ON aa.student_id = s.id
                    WHERE aa.acknowledged = FALSE
                    ORDER BY aa.timestamp DESC
                    LIMIT 50
                ''')
                
                return list(cursor.fetchall())
                
        except Error as e:
            print(f"Error getting active alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """Mark alert as acknowledged"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE attendance_alerts 
                    SET acknowledged = TRUE
                    WHERE id = %s
                ''', (alert_id,))
                
                return cursor.rowcount > 0
                
        except Error as e:
            print(f"Error acknowledging alert: {e}")
            return False
    
    # Statistics and analytics methods
    def get_compliance_statistics(self, start_date: str, end_date: str) -> Dict:
        """Get mask compliance statistics for a date range"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT
                        COUNT(*) AS total_records,
                        SUM(CASE WHEN mask_detected = TRUE THEN 1 ELSE 0 END) AS masked_records,
                        SUM(CASE WHEN mask_violation = TRUE THEN 1 ELSE 0 END) AS violations
                    FROM attendance
                    WHERE date BETWEEN %s AND %s
                ''', (start_date, end_date))
                stats = cursor.fetchone() or {}

                total = stats.get('total_records') or 0
                masked = stats.get('masked_records') or 0
                violations = stats.get('violations') or 0
                compliance_rate = ((masked / total) * 100) if total > 0 else 0.0

                return {
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_records': total,
                    'masked_records': masked,
                    'violations': violations,
                    'compliance_rate': round(compliance_rate, 1)
                }
        except Error as e:
            print(f"Error getting compliance statistics: {e}")
            return {}

    def get_comprehensive_statistics(self, start_date: str, end_date: str) -> Dict:
        """Get comprehensive statistics for reporting"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Basic attendance stats
                cursor.execute('''
                    SELECT COUNT(DISTINCT a.student_id) as total_present,
                           COUNT(*) as total_attendance_records,
                           AVG(a.emotion_confidence) as avg_emotion_confidence,
                           AVG(a.spoofing_score) as avg_spoofing_score
                    FROM attendance a
                    WHERE a.date BETWEEN %s AND %s
                ''', (start_date, end_date))
                
                basic_stats = cursor.fetchone()
                
                # Emotion breakdown
                cursor.execute('''
                    SELECT emotion, COUNT(*) as count
                    FROM emotion_analytics
                    WHERE date BETWEEN %s AND %s
                    GROUP BY emotion
                    ORDER BY count DESC
                ''', (start_date, end_date))
                
                emotion_breakdown = {row['emotion']: row['count'] for row in cursor.fetchall()}
                
                # Lecture stats
                cursor.execute('''
                    SELECT COUNT(*) as total_lectures,
                           AVG(total_attendees) as avg_attendance,
                           AVG(engagement_score) as avg_engagement
                    FROM lecture_sessions
                    WHERE start_time BETWEEN %s AND %s
                ''', (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
                
                lecture_stats = cursor.fetchone()
                
                return {
                    'period': f"{start_date} to {end_date}",
                    'attendance': {
                        'total_present': basic_stats['total_present'] or 0,
                        'total_records': basic_stats['total_attendance_records'] or 0,
                        'avg_emotion_confidence': float(basic_stats['avg_emotion_confidence'] or 0),
                        'avg_spoofing_score': float(basic_stats['avg_spoofing_score'] or 0)
                    },
                    'emotions': emotion_breakdown,
                    'lectures': {
                        'total_lectures': lecture_stats['total_lectures'] or 0,
                        'avg_attendance': float(lecture_stats['avg_attendance'] or 0),
                        'avg_engagement': float(lecture_stats['avg_engagement'] or 0)
                    }
                }
                
        except Error as e:
            print(f"Error getting comprehensive statistics: {e}")
            return {}
    
    # Migration methods
    def migrate_from_sqlite(self, sqlite_db_path: str) -> bool:
        """Migrate data from SQLite database"""
        try:
            import sqlite3
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(sqlite_db_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            with self.get_connection() as mysql_conn:
                mysql_cursor = mysql_conn.cursor()
                
                # Migrate students
                sqlite_cursor.execute("SELECT id, name, face_encoding, image_path FROM students")
                for row in sqlite_cursor.fetchall():
                    mysql_cursor.execute('''
                        INSERT INTO students (id, name, face_encoding, image_path)
                        VALUES (%s, %s, %s, %s)
                    ''', row)
                
                # Migrate attendance
                sqlite_cursor.execute("SELECT student_id, date, time, image_path FROM attendance")
                for row in sqlite_cursor.fetchall():
                    mysql_cursor.execute('''
                        INSERT INTO attendance (student_id, date, time, image_path)
                        VALUES (%s, %s, %s, %s)
                    ''', row)
                
                mysql_conn.commit()
            
            sqlite_conn.close()
            print("Migration from SQLite to MySQL completed successfully!")
            return True
            
        except Exception as e:
            print(f"Migration error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Error as e:
            print(f"Connection test failed: {e}")
            return False

    def add_camera(self, camera_name: str, source: str, location: str = None, ip_address: str = None, is_active: bool = True) -> Optional[int]:
        """Add a camera source to the system."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cameras (name, source, location, ip_address, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        location = VALUES(location),
                        ip_address = VALUES(ip_address),
                        is_active = VALUES(is_active),
                        updated_at = CURRENT_TIMESTAMP
                ''', (camera_name, source, location, ip_address, is_active))
                cursor.execute('SELECT id FROM cameras WHERE source = %s', (source,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Error as e:
            print(f"Error adding camera: {e}")
            return None

    def get_all_cameras(self) -> List[Dict]:
        """Return all registered cameras."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, name, source, location, ip_address, is_active, created_at, updated_at
                    FROM cameras
                    ORDER BY name
                ''')
                return list(cursor.fetchall())
        except Error as e:
            print(f"Error getting cameras: {e}")
            return []

    def get_camera_by_source(self, source: str) -> Optional[Dict]:
        """Return a camera record by its source string."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, name, source, location, ip_address, is_active, created_at, updated_at
                    FROM cameras
                    WHERE source = %s
                    LIMIT 1
                ''', (source,))
                return cursor.fetchone()
        except Error as e:
            print(f"Error getting camera by source: {e}")
            return None

    def get_camera_by_id(self, camera_id: int) -> Optional[Dict]:
        """Return a camera record by its ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT id, name, source, location, ip_address, is_active, created_at, updated_at
                    FROM cameras
                    WHERE id = %s
                ''', (camera_id,))
                return cursor.fetchone()
        except Error as e:
            print(f"Error getting camera by ID: {e}")
            return None

    def add_notification(self, message: str, notification_type: str = "info") -> bool:
        """Add system notification using alerts table"""
        try:
            alert_type = notification_type
            self.create_alert(alert_type, message)
            return True
        except Exception as e:
            print(f"Error adding notification: {e}")
            return False

# Configuration and setup helper
def setup_mysql_database():
    """Setup MySQL database with user input"""
    print("🔧 MySQL Database Setup")
    print("=" * 30)
    
    # Get connection parameters
    host = input("Enter MySQL host (default: localhost): ").strip() or 'localhost'
    user = input("Enter MySQL username (default: root): ").strip() or 'root'
    password = input("Enter MySQL password: ").strip()
    database = input("Enter database name (default: attendance_system): ").strip() or 'attendance_system'
    port = input("Enter MySQL port (default: 3306): ").strip()
    port = int(port) if port else 3306
    
    try:
        # Test connection
        db = MySQLAttendanceDatabase(host=host, user=user, password=password, 
                                   database=database, port=port)
        
        if db.test_connection():
            print("✅ MySQL database connection successful!")
            print(f"📊 Database '{database}' is ready for use!")
            
            # Ask about migration
            if os.path.exists("attendance_system.db"):
                migrate = input("Migrate existing SQLite data? (y/n): ").strip().lower()
                if migrate == 'y':
                    success = db.migrate_from_sqlite("attendance_system.db")
                    if success:
                        print("✅ Migration completed successfully!")
                    else:
                        print("❌ Migration failed!")
            
            return db
        else:
            print("❌ Connection test failed!")
            return None
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return None

if __name__ == "__main__":
    # Test the database setup
    db = setup_mysql_database()
    if db:
        print("🎉 Database is ready to use!")
