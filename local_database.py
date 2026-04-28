import base64
import json
import os
import pickle
import sqlite3
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional


class SQLiteAttendanceDatabase:
    """Local SQLite database for offline attendance and sync queue"""

    def __init__(self, file: str = "offline_attendance.db"):
        self.file = file
        self.connection = sqlite3.connect(self.file, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.init_database()

    def init_database(self):
        cursor = self.connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                face_encoding BLOB,
                image_path TEXT,
                status TEXT DEFAULT 'active',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source TEXT UNIQUE NOT NULL,
                location TEXT,
                ip_address TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                image_path TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                emotion TEXT,
                emotion_confidence REAL,
                spoofing_score REAL,
                is_real_face INTEGER DEFAULT 1,
                camera_id INTEGER,
                mask_detected INTEGER,
                mask_confidence REAL,
                mask_violation INTEGER DEFAULT 0,
                lecture_id TEXT,
                UNIQUE(student_id, date)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                emotion TEXT NOT NULL,
                confidence REAL,
                context TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unknown_faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                face_encoding BLOB,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                student_id INTEGER,
                acknowledged INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lecture_id TEXT NOT NULL,
                student_id INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                duration_seconds INTEGER DEFAULT 0,
                duration TEXT,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                emotion TEXT,
                emotion_confidence REAL,
                head_pose TEXT,
                attention_score REAL,
                gaze_direction TEXT,
                blink_score REAL,
                camera_id INTEGER,
                mask_detected INTEGER DEFAULT 0,
                mask_confidence REAL,
                mask_violation INTEGER DEFAULT 0,
                status TEXT DEFAULT 'present',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity TEXT NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                synced INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.connection.commit()

    def _execute(self, query: str, params: tuple = ()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {key: row[key] for key in row.keys()}

    def _bool(self, value: Optional[int]) -> Optional[bool]:
        if value is None:
            return None
        return bool(value)

    def queue_sync(self, entity: str, action: str, payload: Dict[str, Any]):
        payload_text = json.dumps(payload)
        self._execute(
            '''
            INSERT INTO sync_queue (entity, action, payload, synced)
            VALUES (?, ?, ?, 0)
            ''',
            (entity, action, payload_text)
        )

    def mark_sync_done(self, sync_id: int):
        self._execute(
            '''
            UPDATE sync_queue SET synced = 1 WHERE id = ?
            ''',
            (sync_id,)
        )

    def get_sync_queue(self) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM sync_queue WHERE synced = 0 ORDER BY created_at')
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def create_alert(self, alert_type: str, message: str, student_id: Optional[int] = None) -> Optional[int]:
        cursor = self._execute(
            '''
            INSERT INTO attendance_alerts (alert_type, message, student_id, acknowledged, timestamp)
            VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
            ''',
            (alert_type, message, student_id)
        )

        alert_id = cursor.lastrowid
        self.queue_sync(
            'alert',
            'create',
            {
                'local_id': alert_id,
                'alert_type': alert_type,
                'message': message,
                'student_id': student_id
            }
        )
        return alert_id

    def add_unknown_face(self, image_path: str, face_encoding: Any = None, notes: Optional[str] = None) -> Optional[int]:
        encoding_blob = pickle.dumps(face_encoding) if face_encoding is not None else None
        cursor = self._execute(
            '''
            INSERT INTO unknown_faces (image_path, timestamp, face_encoding, notes)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?)
            ''',
            (image_path, encoding_blob, notes)
        )

        unknown_id = cursor.lastrowid
        self.queue_sync(
            'unknown_face',
            'create',
            {
                'local_id': unknown_id,
                'image_path': image_path,
                'notes': notes
            }
        )
        return unknown_id

    def add_student_advanced(self, name: str, face_encoding: Any, image_path: Optional[str] = None,
                             notes: Optional[str] = None) -> Optional[int]:
        encoding_blob = pickle.dumps(face_encoding) if face_encoding is not None else None

        cursor = self._execute(
            '''
            INSERT INTO students (name, face_encoding, image_path, status, notes, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                face_encoding = excluded.face_encoding,
                image_path = excluded.image_path,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (name, encoding_blob, image_path, notes)
        )

        cursor = self._execute('SELECT id FROM students WHERE name = ?', (name,))
        student_id = cursor.fetchone()[0]

        self.queue_sync(
            'student',
            'upsert',
            {
                'local_id': student_id,
                'name': name,
                'face_encoding': base64.b64encode(encoding_blob).decode() if encoding_blob else None,
                'image_path': image_path,
                'notes': notes
            }
        )

        return student_id

    def add_student(self, name: str, face_encoding: Any, image_path: Optional[str] = None,
                    notes: Optional[str] = None) -> Optional[int]:
        return self.add_student_advanced(name, face_encoding, image_path, notes)

    def get_all_students(self) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(
            '''
            SELECT id, name, face_encoding, image_path, status, notes, created_at, updated_at
            FROM students WHERE status = 'active' ORDER BY name
            '''
        )
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

    def get_student_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(
            '''
            SELECT id, name, face_encoding, image_path, status, notes, created_at, updated_at
            FROM students WHERE name = ? AND status = 'active'
            ''',
            (name,)
        )
        row = cursor.fetchone()
        if not row:
            return None

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

    def add_camera(self, camera_name: str, source: str, location: str = None,
                   ip_address: str = None, is_active: bool = True) -> Optional[int]:
        cursor = self._execute(
            '''
            INSERT INTO cameras (name, source, location, ip_address, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(source) DO UPDATE SET
                name = excluded.name,
                location = excluded.location,
                ip_address = excluded.ip_address,
                is_active = excluded.is_active,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (camera_name, source, location, ip_address, 1 if is_active else 0)
        )

        cursor = self._execute('SELECT id FROM cameras WHERE source = ?', (source,))
        camera_id = cursor.fetchone()[0]

        self.queue_sync(
            'camera',
            'upsert',
            {
                'local_id': camera_id,
                'name': camera_name,
                'source': source,
                'location': location,
                'ip_address': ip_address,
                'is_active': bool(is_active)
            }
        )

        return camera_id

    def get_all_cameras(self) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute('SELECT id, name, source, location, ip_address, is_active FROM cameras ORDER BY id')
        cameras = []
        for row in cursor.fetchall():
            cameras.append({
                'id': row['id'],
                'name': row['name'],
                'source': row['source'],
                'location': row['location'],
                'ip_address': row['ip_address'],
                'is_active': bool(row['is_active'])
            })
        return cameras

    def get_camera_by_source(self, source: str) -> Optional[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute('SELECT id, name, source, location, ip_address, is_active FROM cameras WHERE source = ?', (source,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': row['id'],
            'name': row['name'],
            'source': row['source'],
            'location': row['location'],
            'ip_address': row['ip_address'],
            'is_active': bool(row['is_active'])
        }

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
        student = self.get_student_by_name(self.get_student_name_by_id(student_id)) if student_id else None
        if not student:
            return False, 'Student not found'

        if student['status'] != 'active':
            return False, f"Student is not active (status: {student['status']})"

        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id FROM attendance WHERE student_id = ? AND date = ?
            ''', (student_id, date_str))
        if cursor.fetchone():
            return False, f"Attendance already marked for {date_str}"

        self._execute(
            '''
            INSERT INTO attendance
            (student_id, date, time, image_path, emotion, emotion_confidence,
             spoofing_score, is_real_face, camera_id, mask_detected, mask_confidence,
             mask_violation, lecture_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                student_id, date_str, time_str, image_path, emotion,
                emotion_confidence, spoofing_score,
                1 if is_real_face else 0 if is_real_face is not None else None,
                camera_id,
                1 if mask_detected else 0 if mask_detected is not None else None,
                mask_confidence,
                1 if mask_violation else 0,
                lecture_id
            )
        )

        if emotion is not None:
            self._execute(
                '''
                INSERT INTO emotion_analytics (student_id, date, time, emotion, confidence, context)
                VALUES (?, ?, ?, ?, ?, 'attendance')
                ''',
                (student_id, date_str, time_str, emotion, emotion_confidence)
            )

        camera = self.get_camera_by_id(camera_id) if camera_id else None
        queue_payload = {
            'student_name': student['name'],
            'date': date_str,
            'time': time_str,
            'image_path': image_path,
            'emotion': emotion,
            'emotion_confidence': emotion_confidence,
            'spoofing_score': spoofing_score,
            'is_real_face': is_real_face,
            'camera_source': camera['source'] if camera else None,
            'camera_name': camera['name'] if camera else None,
            'camera_location': camera['location'] if camera else None,
            'camera_ip_address': camera['ip_address'] if camera else None,
            'mask_detected': mask_detected,
            'mask_confidence': mask_confidence,
            'mask_violation': mask_violation,
            'lecture_id': lecture_id
        }
        self.queue_sync('attendance', 'create', queue_payload)

        return True, 'Attendance marked successfully (offline)'

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
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id FROM lecture_attendance
            WHERE lecture_id = ? AND student_id = ? AND status = 'present'
            ORDER BY id DESC
            LIMIT 1
        ''', (lecture_id, student_id))
        row = cursor.fetchone()

        entry_time_str = entry_time.strftime('%H:%M:%S') if isinstance(entry_time, time) else str(entry_time)
        last_seen_str = datetime.now().isoformat(sep=' ')
        mask_flag = 1 if mask_detected else 0 if mask_detected is not None else None
        violation_flag = 1 if mask_violation else 0

        if row:
            attendance_id = row[0]
            self._execute('''
                UPDATE lecture_attendance
                SET last_seen = ?, emotion = ?, emotion_confidence = ?, head_pose = ?,
                    attention_score = ?, gaze_direction = ?, blink_score = ?,
                    camera_id = ?, mask_detected = ?, mask_confidence = ?,
                    mask_violation = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                last_seen_str, emotion, emotion_confidence, head_pose,
                attention_score, gaze_direction, blink_score,
                camera_id, mask_flag, mask_confidence,
                violation_flag, attendance_id
            ))
            return attendance_id

        self._execute('''
            INSERT INTO lecture_attendance
            (lecture_id, student_id, entry_time, last_seen, emotion, emotion_confidence,
             head_pose, attention_score, gaze_direction, blink_score, camera_id,
             mask_detected, mask_confidence, mask_violation, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (
            lecture_id, student_id, entry_time_str, last_seen_str, emotion, emotion_confidence,
            head_pose, attention_score, gaze_direction, blink_score, camera_id,
            mask_flag, mask_confidence, violation_flag
        ))
        return cursor.lastrowid

    def close_lecture_presence(self, lecture_id: str, student_id: int, exit_time: datetime.time) -> bool:
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id, entry_time FROM lecture_attendance
            WHERE lecture_id = ? AND student_id = ? AND status = 'present'
            ORDER BY id DESC
            LIMIT 1
        ''', (lecture_id, student_id))
        row = cursor.fetchone()
        if not row:
            return False

        attendance_id, entry_time = row
        if isinstance(entry_time, str):
            entry_time = datetime.strptime(entry_time, '%H:%M:%S').time()

        exit_time_str = exit_time.strftime('%H:%M:%S') if isinstance(exit_time, time) else str(exit_time)
        seconds = int(
            (datetime.combine(datetime.today(), exit_time) -
             datetime.combine(datetime.today(), entry_time)).total_seconds()
        )
        duration_str = str(timedelta(seconds=max(seconds, 0)))
        last_seen_str = datetime.now().isoformat(sep=' ')

        self._execute('''
            UPDATE lecture_attendance
            SET exit_time = ?, duration_seconds = ?, duration = ?,
                status = 'left', last_seen = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (exit_time_str, seconds, duration_str, last_seen_str, attendance_id))

        return True

    def update_lecture_session_attendance(self, lecture_id: str) -> bool:
        return True

    def get_student_name_by_id(self, student_id: int) -> Optional[str]:
        cursor = self.connection.cursor()
        cursor.execute('SELECT name FROM students WHERE id = ?', (student_id,))
        row = cursor.fetchone()
        return row['name'] if row else None

    def get_camera_by_id(self, camera_id: int) -> Optional[Dict[str, Any]]:
        if not camera_id:
            return None
        cursor = self.connection.cursor()
        cursor.execute('SELECT id, name, source, location, ip_address, is_active FROM cameras WHERE id = ?', (camera_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': row['id'],
            'name': row['name'],
            'source': row['source'],
            'location': row['location'],
            'ip_address': row['ip_address'],
            'is_active': bool(row['is_active'])
        }

    def get_attendance_with_emotions(self, date_str: str) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(
            '''
            SELECT s.name, a.time, a.image_path, a.timestamp, a.emotion,
                   a.emotion_confidence, a.spoofing_score, a.is_real_face,
                   a.camera_id, a.mask_detected, a.mask_confidence, a.mask_violation
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = ?
            ORDER BY a.time
            ''',
            (date_str,)
        )
        records = []
        for row in cursor.fetchall():
            records.append({
                'name': row['name'],
                'time': row['time'],
                'image_path': row['image_path'],
                'timestamp': row['timestamp'],
                'emotion': row['emotion'],
                'emotion_confidence': row['emotion_confidence'],
                'spoofing_score': row['spoofing_score'],
                'is_real_face': bool(row['is_real_face']) if row['is_real_face'] is not None else None,
                'camera_id': row['camera_id'],
                'mask_detected': bool(row['mask_detected']) if row['mask_detected'] is not None else None,
                'mask_confidence': row['mask_confidence'],
                'mask_violation': bool(row['mask_violation']) if row['mask_violation'] is not None else None
            })
        return records

    def get_attendance_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(
            '''
            SELECT s.name, a.date, a.time, a.image_path, a.timestamp, a.emotion,
                   a.mask_detected, a.mask_confidence, a.mask_violation
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date BETWEEN ? AND ?
            ORDER BY a.date, a.time
            ''',
            (start_date, end_date)
        )
        records = []
        for row in cursor.fetchall():
            records.append({
                'name': row['name'],
                'date': row['date'],
                'time': row['time'],
                'image_path': row['image_path'],
                'timestamp': row['timestamp'],
                'emotion': row['emotion'],
                'mask_detected': bool(row['mask_detected']) if row['mask_detected'] is not None else None,
                'mask_confidence': row['mask_confidence'],
                'mask_violation': bool(row['mask_violation']) if row['mask_violation'] is not None else None
            })
        return records
