"""Business logic for attendance, lectures, and face sightings."""
from __future__ import annotations

import json
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.database_core_mysql import MySQLAttendanceDatabase
from core.email_service import EmailNotifier, load_email_config
from core.features_ai_advanced import AntiSpoofing, MaskDetector
from core.pdf_export import export_attendance_report_pdf
from core.paths import REPORTS_DIR


def load_settings() -> Dict:
    root = Path(__file__).resolve().parent.parent
    candidates = [
        root / "config" / "attendance_settings.json",
        root / "system_settings.json",
        root / "core" / "attendance_settings.json",
    ]
    path = next((p for p in candidates if p.exists()), candidates[0])
    defaults = {
        "late_threshold_minutes": 15,
        "require_real_face": True,
        "require_mask": False,
        "session_grace_minutes": 5,
    }
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {**defaults, **json.load(f)}
    except (OSError, json.JSONDecodeError):
        return defaults


class AttendanceService:
    def __init__(self, db: MySQLAttendanceDatabase):
        self.db = db
        self.settings = load_settings()
        self.anti_spoofing = AntiSpoofing()
        self.mask_detector = MaskDetector()
        self.active_lecture_id: Optional[str] = None
        self.lecture_start_time: Optional[datetime] = None
        self.lecture_late_threshold: int = self.settings["late_threshold_minutes"]
        self.lecture_section: Optional[str] = None
        self.session_present_ids: set = set()
        self.email_notifier = EmailNotifier()
        self.last_lecture_name: Optional[str] = None
        self._refresh_active_lecture()

    def _refresh_active_lecture(self) -> None:
        lec = self.db.get_active_lecture()
        if lec:
            self.active_lecture_id = lec["id"]
            self.lecture_start_time = lec.get("start_time") or datetime.now()
            self.lecture_late_threshold = lec.get("late_threshold_minutes") or 15
            self.lecture_section = lec.get("section")

    def start_lecture(
        self,
        name: str,
        course_code: str = "",
        instructor: str = "",
        section: Optional[str] = None,
        late_threshold: Optional[int] = None,
    ) -> Tuple[bool, str]:
        lecture_id = f"lec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        threshold = late_threshold or self.settings["late_threshold_minutes"]
        ok = self.db.create_lecture_session_v2(
            lecture_id, name, course_code, instructor, section, threshold
        )
        if ok:
            self.active_lecture_id = lecture_id
            self.last_lecture_name = name
            self.lecture_start_time = datetime.now()
            self.lecture_late_threshold = threshold
            self.lecture_section = section
            self.session_present_ids = set()
            return True, lecture_id
        return False, "فشل بدء المحاضرة"

    def end_lecture(self) -> Tuple[bool, str, Dict]:
        if not self.active_lecture_id:
            return False, "لا توجد محاضرة نشطة", {}
        marked = self.db.finalize_lecture_absences(
            self.active_lecture_id,
            list(self.session_present_ids),
            self.lecture_section,
        )
        lecture_id_done = self.active_lecture_id
        lecture_title = self.last_lecture_name or lecture_id_done
        board = self.db.get_attendance_board(date.today().isoformat(), lecture_id_done)
        report = self.export_absence_report()
        self.db.end_lecture_session(lecture_id_done, emotions_summary={})

        email_ok, email_msg = False, "البريد معطّل"
        email_cfg = load_email_config()
        if email_cfg.get("enabled") and email_cfg.get("notify_on_lecture_end"):
            email_ok, email_msg = self.email_notifier.send_attendance_report(
                report,
                lecture_name=lecture_title,
                include_student_emails=email_cfg.get("notify_students_absent")
                or email_cfg.get("notify_students_late"),
            )

        summary = {
            "lecture_id": lecture_id_done,
            "absent_marked": marked,
            "board": board,
            "email_sent": email_ok,
            "email_message": email_msg,
        }
        self.active_lecture_id = None
        self.lecture_start_time = None
        self.last_lecture_name = None
        self.session_present_ids = set()
        msg = f"انتهت المحاضرة — غياب: {marked}"
        if email_cfg.get("enabled"):
            msg += f" | بريد: {email_msg}"
        return True, msg, summary

    def send_email_report(
        self,
        date_str: Optional[str] = None,
        include_students: bool = False,
    ) -> Tuple[bool, str]:
        report = self.export_absence_report(date_str)
        return self.email_notifier.send_attendance_report(
            report,
            include_student_emails=include_students,
        )

    def send_test_email(self) -> Tuple[bool, str]:
        return self.email_notifier.send_test_email()

    def export_report_pdf(
        self,
        date_str: Optional[str] = None,
        lecture_name: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Tuple[bool, str]:
        report = self.export_absence_report(date_str)
        lec = lecture_name or self.last_lecture_name
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        return export_attendance_report_pdf(report, output_path, lec)

    def _compute_late_status(self, now: datetime) -> Tuple[str, int]:
        if not self.lecture_start_time:
            return "present", 0
        delta = now - self.lecture_start_time
        minutes = int(delta.total_seconds() / 60)
        if minutes > self.lecture_late_threshold:
            return "late", minutes - self.lecture_late_threshold
        return "present", 0

    def process_face_sighting(
        self,
        student_name: str,
        face_crop,
        frame,
        emotion: str = "neutral",
        emotion_confidence: float = 0.0,
        image_path: Optional[str] = None,
    ) -> Tuple[bool, str, Dict]:
        student = self.db.get_student_by_name_v2(student_name) or self.db.get_student_by_name(student_name)
        if not student:
            return False, "student_not_found", {}

        if self.settings.get("require_real_face", True):
            is_real, spoof_score = self.anti_spoofing.is_real_face(face_crop, frame)
            if not is_real:
                return False, "spoofing_rejected", {"spoofing_score": spoof_score}

        mask_detected, mask_confidence, mask_violation = None, None, False
        if face_crop is not None and getattr(face_crop, "size", 0) > 0:
            mask_result = self.mask_detector.detect_mask(face_crop)
            mask_detected = mask_result.get("wearing_mask", False)
            mask_confidence = mask_result.get("confidence", 0.0)
            if self.settings.get("require_mask", False) and not mask_detected:
                mask_violation = True
                return False, "mask_required", mask_result

        now = datetime.now()
        date_str = now.date().isoformat()
        time_str = now.time().strftime("%H:%M:%S")
        status, late_mins = self._compute_late_status(now)

        ok, msg = self.db.record_attendance_sighting(
            student_id=student["id"],
            date_str=date_str,
            time_str=time_str,
            attendance_status=status,
            image_path=image_path,
            emotion=emotion,
            emotion_confidence=emotion_confidence,
            is_real_face=True,
            mask_detected=mask_detected,
            mask_confidence=mask_confidence,
            mask_violation=mask_violation,
            lecture_id=self.active_lecture_id,
            late_minutes=late_mins,
        )

        if self.active_lecture_id:
            self.session_present_ids.add(student["id"])
            entry_time = now.time()
            self.db.create_or_update_lecture_presence(
                self.active_lecture_id,
                student["id"],
                entry_time,
                emotion=emotion,
                emotion_confidence=emotion_confidence,
                mask_detected=mask_detected,
                mask_confidence=mask_confidence,
                mask_violation=mask_violation,
            )

        return ok, msg, {
            "status": status,
            "late_minutes": late_mins,
            "student_id": student["id"],
        }

    def get_live_board(self) -> Dict:
        return self.db.get_attendance_board(
            date.today().isoformat(),
            self.active_lecture_id,
        )

    def export_absence_report(self, date_str: Optional[str] = None) -> Dict:
        d = date_str or date.today().isoformat()
        board = self.db.get_attendance_board(d)
        return {
            "date": d,
            "generated_at": datetime.now().isoformat(),
            "totals": board["totals"],
            "absent_list": board["absent"],
            "late_list": board["late"],
            "present_list": board["present"],
            "excused_list": board["excused"],
        }
