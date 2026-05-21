"""Extended DB schema and methods for attendance v2."""
from __future__ import annotations

import json
import pickle
import shutil
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mysql.connector import Error

from core.paths import KNOWN_FACES_DIR, UNKNOWN_FACES_DIR


class AttendanceDBExtensions:
    """Mixin: student profiles, status, schedule, lecture absence."""

    def ensure_v2_schema(self) -> None:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self._ensure_student_profile_columns(cursor)
                self._ensure_attendance_status_columns(cursor)
                self._create_class_schedule_table(cursor)
                self._create_daily_absence_table(cursor)
                self._ensure_lecture_session_columns(cursor)
                self._ensure_unknown_temp_id(cursor)
                conn.commit()
        except Error as e:
            print(f"V2 schema migration warning: {e}")

    def _column_exists(self, cursor, table: str, column: str) -> bool:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        return cursor.fetchone()[0] > 0

    def _ensure_student_profile_columns(self, cursor) -> None:
        for col, definition in [
            ("student_code", "VARCHAR(50) NULL"),
            ("section", "VARCHAR(100) NULL"),
            ("year_level", "VARCHAR(50) NULL"),
            ("group_name", "VARCHAR(100) NULL"),
        ]:
            if not self._column_exists(cursor, "students", col):
                cursor.execute(f"ALTER TABLE students ADD COLUMN {col} {definition}")

    def _ensure_attendance_status_columns(self, cursor) -> None:
        if not self._column_exists(cursor, "attendance", "attendance_status"):
            cursor.execute(
                """
                ALTER TABLE attendance ADD COLUMN attendance_status
                ENUM('present','absent','late','excused') DEFAULT 'present'
                """
            )
        for col, definition in [
            ("check_in_time", "TIME NULL"),
            ("check_out_time", "TIME NULL"),
            ("late_minutes", "INT DEFAULT 0"),
            ("updated_at_ts", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ]:
            if not self._column_exists(cursor, "attendance", col):
                cursor.execute(f"ALTER TABLE attendance ADD COLUMN {col} {definition}")

    def _create_class_schedule_table(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS class_schedule (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_name VARCHAR(255) NOT NULL,
                course_code VARCHAR(50),
                section VARCHAR(100),
                day_of_week TINYINT NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                instructor VARCHAR(255),
                room VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_day (day_of_week),
                INDEX idx_section (section)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    def _create_daily_absence_table(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_absence (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                date DATE NOT NULL,
                lecture_id VARCHAR(100) NULL,
                status ENUM('absent','excused') DEFAULT 'absent',
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE KEY uniq_student_date_lecture (student_id, date, lecture_id),
                INDEX idx_date (date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    def _ensure_lecture_session_columns(self, cursor) -> None:
        for col, definition in [
            ("section", "VARCHAR(100) NULL"),
            ("late_threshold_minutes", "INT DEFAULT 15"),
            ("roster_student_ids", "JSON NULL"),
        ]:
            if not self._column_exists(cursor, "lecture_sessions", col):
                cursor.execute(f"ALTER TABLE lecture_sessions ADD COLUMN {col} {definition}")

    def _ensure_unknown_temp_id(self, cursor) -> None:
        if not self._column_exists(cursor, "unknown_faces", "temp_id"):
            cursor.execute("ALTER TABLE unknown_faces ADD COLUMN temp_id VARCHAR(50) NULL")

    def _student_row_to_dict(self, row: Dict) -> Dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "student_code": row.get("student_code"),
            "section": row.get("section"),
            "year_level": row.get("year_level"),
            "group_name": row.get("group_name"),
            "face_encoding": pickle.loads(row["face_encoding"]) if row.get("face_encoding") else None,
            "image_path": row.get("image_path"),
            "status": row.get("status"),
            "notes": row.get("notes"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }

    def _student_select_sql(self) -> str:
        return """
            SELECT id, name, student_code, section, year_level, group_name,
                   face_encoding, image_path, status, notes, created_at, updated_at
            FROM students
        """

    def add_student_with_profile(
        self,
        name: str,
        face_encoding: Any,
        image_path: Optional[str] = None,
        notes: Optional[str] = None,
        student_code: Optional[str] = None,
        section: Optional[str] = None,
        year_level: Optional[str] = None,
        group_name: Optional[str] = None,
    ) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                encoding_blob = pickle.dumps(face_encoding) if face_encoding is not None else None
                cursor.execute(
                    """
                    INSERT INTO students
                    (name, face_encoding, image_path, notes, student_code, section, year_level, group_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        face_encoding = COALESCE(VALUES(face_encoding), face_encoding),
                        image_path = VALUES(image_path),
                        notes = VALUES(notes),
                        student_code = VALUES(student_code),
                        section = VALUES(section),
                        year_level = VALUES(year_level),
                        group_name = VALUES(group_name),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (name, encoding_blob, image_path, notes, student_code, section, year_level, group_name),
                )
                cursor.execute("SELECT id FROM students WHERE name = %s", (name,))
                student_id = cursor.fetchone()[0]
                if encoding_blob:
                    cursor.execute(
                        """
                        INSERT INTO face_data (student_id, face_encoding, image_path, is_primary, quality_score)
                        VALUES (%s, %s, %s, TRUE, 0.8)
                        """,
                        (student_id, encoding_blob, image_path),
                    )
                return student_id
        except Error as e:
            print(f"Error add_student_with_profile: {e}")
            return None

    def get_students_filtered(self, section: Optional[str] = None) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                sql = self._student_select_sql() + " WHERE status = 'active'"
                params: tuple = ()
                if section:
                    sql += " AND section = %s"
                    params = (section,)
                sql += " ORDER BY name"
                cursor.execute(sql, params)
                return [self._student_row_to_dict(r) for r in cursor.fetchall()]
        except Error as e:
            print(f"Error get_students_filtered: {e}")
            return []

    def get_all_students_v2(self) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(self._student_select_sql() + " WHERE status = 'active' ORDER BY name")
                return [self._student_row_to_dict(r) for r in cursor.fetchall()]
        except Error as e:
            print(f"Error get_all_students_v2: {e}")
            return []

    def get_student_by_name_v2(self, name: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    self._student_select_sql() + " WHERE name = %s AND status = 'active'",
                    (name,),
                )
                row = cursor.fetchone()
                return self._student_row_to_dict(row) if row else None
        except Error as e:
            print(f"Error get_student_by_name_v2: {e}")
            return None

    def record_attendance_sighting(
        self,
        student_id: int,
        date_str: str,
        time_str: str,
        attendance_status: str = "present",
        image_path: Optional[str] = None,
        emotion: Optional[str] = None,
        emotion_confidence: Optional[float] = None,
        spoofing_score: Optional[float] = None,
        is_real_face: bool = True,
        mask_detected: Optional[bool] = None,
        mask_confidence: Optional[float] = None,
        mask_violation: bool = False,
        lecture_id: Optional[str] = None,
        late_minutes: int = 0,
    ) -> Tuple[bool, str]:
        """Insert or update daily attendance (check-in / check-out)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, attendance_status, check_in_time FROM attendance WHERE student_id = %s AND date = %s",
                    (student_id, date_str),
                )
                row = cursor.fetchone()
                if row:
                    cursor.execute(
                        """
                        UPDATE attendance SET
                            check_out_time = %s, time = %s, image_path = COALESCE(%s, image_path),
                            emotion = COALESCE(%s, emotion), emotion_confidence = COALESCE(%s, emotion_confidence),
                            spoofing_score = COALESCE(%s, spoofing_score), is_real_face = %s,
                            mask_detected = COALESCE(%s, mask_detected),
                            mask_confidence = COALESCE(%s, mask_confidence),
                            mask_violation = %s, lecture_id = COALESCE(%s, lecture_id)
                        WHERE id = %s
                        """,
                        (
                            time_str, time_str, image_path, emotion, emotion_confidence,
                            spoofing_score, is_real_face, mask_detected, mask_confidence,
                            mask_violation, lecture_id, row["id"],
                        ),
                    )
                    return True, "checkout_updated"

                cursor.execute(
                    """
                    INSERT INTO attendance
                    (student_id, date, time, check_in_time, check_out_time, image_path, emotion,
                     emotion_confidence, spoofing_score, is_real_face, mask_detected, mask_confidence,
                     mask_violation, lecture_id, attendance_status, late_minutes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        student_id, date_str, time_str, time_str, time_str, image_path, emotion,
                        emotion_confidence, spoofing_score, is_real_face, mask_detected, mask_confidence,
                        mask_violation, lecture_id, attendance_status, late_minutes,
                    ),
                )
                return True, "checkin_recorded"
        except Error as e:
            return False, str(e)

    def get_attendance_board(self, date_str: str, lecture_id: Optional[str] = None) -> Dict:
        students = self.get_students_filtered()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT a.student_id, a.attendance_status, a.check_in_time, a.check_out_time,
                           a.time, a.emotion, a.late_minutes, s.name, s.student_code, s.section
                    FROM attendance a
                    JOIN students s ON s.id = a.student_id
                    WHERE a.date = %s
                    """,
                    (date_str,),
                )
                records = {r["student_id"]: r for r in cursor.fetchall()}

                cursor.execute(
                    "SELECT student_id, status, reason FROM daily_absence WHERE date = %s",
                    (date_str,),
                )
                absences = {r["student_id"]: r for r in cursor.fetchall()}
        except Error as e:
            print(f"get_attendance_board error: {e}")
            records, absences = {}, {}

        present, late, absent, excused, unknown = [], [], [], [], []
        for st in students:
            sid = st["id"]
            rec = records.get(sid)
            ab = absences.get(sid)
            entry = {
                "id": sid,
                "name": st["name"],
                "student_code": st.get("student_code") or "",
                "section": st.get("section") or "",
            }
            if rec:
                entry.update(rec)
                status = rec.get("attendance_status") or "present"
                if status == "late":
                    late.append(entry)
                elif status == "excused":
                    excused.append(entry)
                else:
                    present.append(entry)
            elif ab and ab.get("status") == "excused":
                entry["reason"] = ab.get("reason")
                excused.append(entry)
            else:
                absent.append(entry)

        return {
            "date": date_str,
            "lecture_id": lecture_id,
            "present": present,
            "late": late,
            "absent": absent,
            "excused": excused,
            "totals": {
                "students": len(students),
                "present": len(present),
                "late": len(late),
                "absent": len(absent),
                "excused": len(excused),
            },
        }

    def set_manual_attendance_status(
        self,
        student_id: int,
        date_str: str,
        status: str,
        time_str: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Tuple[bool, str]:
        now_t = time_str or datetime.now().strftime("%H:%M:%S")
        if status in ("present", "late"):
            return self.record_attendance_sighting(
                student_id, date_str, now_t, attendance_status=status
            )
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM attendance WHERE student_id = %s AND date = %s",
                    (student_id, date_str),
                )
                abs_status = "excused" if status == "excused" else "absent"
                cursor.execute(
                    """
                    INSERT INTO daily_absence (student_id, date, status, reason)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE status = VALUES(status), reason = VALUES(reason)
                    """,
                    (student_id, date_str, abs_status, reason),
                )
                return True, status
        except Error as e:
            return False, str(e)

    def finalize_lecture_absences(
        self,
        lecture_id: str,
        present_student_ids: List[int],
        section: Optional[str] = None,
    ) -> int:
        students = self.get_students_filtered(section)
        today = date.today().isoformat()
        marked = 0
        present_set = set(present_student_ids)
        for st in students:
            if st["id"] not in present_set:
                ok, _ = self.set_manual_attendance_status(
                    st["id"], today, "absent", reason=f"auto_absent_lecture:{lecture_id}"
                )
                if ok:
                    marked += 1
        return marked

    def add_schedule_entry(
        self,
        course_name: str,
        course_code: str,
        section: str,
        day_of_week: int,
        start_time: str,
        end_time: str,
        instructor: str = "",
        room: str = "",
    ) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO class_schedule
                    (course_name, course_code, section, day_of_week, start_time, end_time, instructor, room)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (course_name, course_code, section, day_of_week, start_time, end_time, instructor, room),
                )
                return True
        except Error as e:
            print(f"add_schedule_entry: {e}")
            return False

    def get_schedule(self, day_of_week: Optional[int] = None) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                if day_of_week is not None:
                    cursor.execute(
                        "SELECT * FROM class_schedule WHERE is_active = TRUE AND day_of_week = %s ORDER BY start_time",
                        (day_of_week,),
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM class_schedule WHERE is_active = TRUE ORDER BY day_of_week, start_time"
                    )
                return list(cursor.fetchall())
        except Error as e:
            print(f"get_schedule: {e}")
            return []

    def get_unknown_faces_with_temp(self, limit: int = 50) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT id, image_path, timestamp, processed, notes, temp_id
                    FROM unknown_faces WHERE processed = FALSE
                    ORDER BY timestamp DESC LIMIT %s
                    """,
                    (limit,),
                )
                return list(cursor.fetchall())
        except Error as e:
            print(f"get_unknown_faces_with_temp: {e}")
            return []

    def promote_unknown_temp_to_student(
        self,
        temp_id: str,
        name: str,
        face_encoding: Any,
        student_code: Optional[str] = None,
        section: Optional[str] = None,
        year_level: Optional[str] = None,
        group_name: Optional[str] = None,
    ) -> Optional[int]:
        unknown_dir = UNKNOWN_FACES_DIR / temp_id
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.strip())
        known_dir = KNOWN_FACES_DIR / safe
        known_dir.mkdir(parents=True, exist_ok=True)
        if unknown_dir.exists():
            for img in unknown_dir.glob("*"):
                shutil.copy2(img, known_dir / img.name)
        image_path = str(known_dir)
        student_id = self.add_student_with_profile(
            name, face_encoding, image_path, notes=f"promoted_from:{temp_id}",
            student_code=student_code, section=section, year_level=year_level, group_name=group_name,
        )
        if student_id:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE unknown_faces SET processed = TRUE WHERE notes LIKE %s OR temp_id = %s",
                        (f"%{temp_id}%", temp_id),
                    )
            except Error:
                pass
        return student_id

    def get_attendance_with_emotions_v2(self, date_str: str) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT s.name, s.student_code, s.section, a.time, a.check_in_time, a.check_out_time,
                           a.attendance_status, a.late_minutes, a.emotion, a.is_real_face, a.image_path
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.date = %s
                    ORDER BY a.time
                    """,
                    (date_str,),
                )
                return list(cursor.fetchall())
        except Error as e:
            print(f"get_attendance_with_emotions_v2: {e}")
            return []

    def create_lecture_session_v2(
        self,
        lecture_id: str,
        name: str,
        course_code: str,
        instructor: str,
        section: Optional[str] = None,
        late_threshold_minutes: int = 15,
    ) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO lecture_sessions
                    (id, name, course_code, instructor, start_time, section, late_threshold_minutes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (lecture_id, name, course_code, instructor, datetime.now(), section, late_threshold_minutes),
                )
                return True
        except Error as e:
            print(f"create_lecture_session_v2: {e}")
            return False

    def get_active_lecture(self) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT id, name, course_code, instructor, section, late_threshold_minutes, start_time
                    FROM lecture_sessions WHERE end_time IS NULL
                    ORDER BY start_time DESC LIMIT 1
                    """
                )
                return cursor.fetchone()
        except Error as e:
            print(f"get_active_lecture: {e}")
            return None
