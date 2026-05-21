"""Manage known/unknown face captures with per-person folders."""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False

from core.paths import (
    ATTENDANCE_IMAGES_DIR,
    KNOWN_FACES_DIR,
    UNKNOWN_COUNTER_FILE,
    UNKNOWN_FACES_DIR,
    ensure_data_dirs,
)


class FaceCaptureManager:
    """Save captures in known_faces/<name>/ or unknown_faces/temp_XXX/."""

    def __init__(
        self,
        known_dir: Path = KNOWN_FACES_DIR,
        unknown_dir: Path = UNKNOWN_FACES_DIR,
        attendance_dir: Path = ATTENDANCE_IMAGES_DIR,
        save_cooldown: float = 3.0,
        match_tolerance: float = 0.55,
    ):
        ensure_data_dirs()
        self.known_dir = Path(known_dir)
        self.unknown_dir = Path(unknown_dir)
        self.attendance_dir = Path(attendance_dir)
        self.save_cooldown = save_cooldown
        self.match_tolerance = match_tolerance

        self.known_dir.mkdir(parents=True, exist_ok=True)
        self.unknown_dir.mkdir(parents=True, exist_ok=True)
        self.attendance_dir.mkdir(parents=True, exist_ok=True)

        self._last_saved: Dict[str, float] = {}
        self._session_unknown: List[Dict[str, Any]] = []
        self._temp_counter = self._load_counter()

    @staticmethod
    def safe_folder_name(name: str) -> str:
        cleaned = re.sub(r"[^\w\u0600-\u06FF\-]+", "_", name.strip())
        return cleaned or "unnamed"

    def _load_counter(self) -> int:
        try:
            if UNKNOWN_COUNTER_FILE.exists():
                with open(UNKNOWN_COUNTER_FILE, "r", encoding="utf-8") as f:
                    return int(json.load(f).get("counter", 0))
        except (json.JSONDecodeError, OSError, ValueError):
            pass
        return len(list(self.unknown_dir.glob("temp_*")))

    def _save_counter(self) -> None:
        UNKNOWN_COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(UNKNOWN_COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump({"counter": self._temp_counter}, f)

    def _next_temp_id(self) -> str:
        self._temp_counter += 1
        self._save_counter()
        return f"temp_{self._temp_counter:03d}"

    def _should_save(self, key: str) -> bool:
        now = time.time()
        last = self._last_saved.get(key, 0)
        if now - last < self.save_cooldown:
            return False
        self._last_saved[key] = now
        return True

    def find_match_index(
        self,
        face_encoding: Any,
        encodings: List[Any],
        tolerance: Optional[float] = None,
    ) -> Optional[int]:
        if not FACE_RECOGNITION_AVAILABLE or not encodings:
            return None
        tol = tolerance if tolerance is not None else self.match_tolerance
        distances = face_recognition.face_distance(encodings, face_encoding)
        best_idx = int(distances.argmin())
        if distances[best_idx] <= tol:
            return best_idx
        return None

    def match_known(
        self,
        face_encoding: Any,
        known_encodings: List[Any],
        known_names: List[str],
    ) -> Optional[str]:
        idx = self.find_match_index(face_encoding, known_encodings)
        if idx is not None and idx < len(known_names):
            return known_names[idx]
        return None

    def match_or_register_unknown(self, face_encoding: Any) -> Tuple[str, bool]:
        """Return (temp_id, is_new) for unknown face in current camera session."""
        idx = self.find_match_index(
            face_encoding,
            [entry["encoding"] for entry in self._session_unknown],
            tolerance=0.5,
        )
        if idx is not None:
            return self._session_unknown[idx]["temp_id"], False

        temp_id = self._next_temp_id()
        self._session_unknown.append({"encoding": face_encoding, "temp_id": temp_id})
        return temp_id, True

    def save_face_image(
        self,
        folder: Path,
        frame,
        prefix: str = "capture",
    ) -> str:
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.jpg"
        path = folder / filename
        import cv2

        cv2.imwrite(str(path), frame)
        return str(path)

    def capture_known(self, student_name: str, frame) -> Optional[str]:
        key = f"known:{student_name}"
        if not self._should_save(key):
            return None
        folder = self.known_dir / self.safe_folder_name(student_name)
        return self.save_face_image(folder, frame, prefix="pass")

    def capture_unknown(self, temp_id: str, frame) -> Optional[str]:
        key = f"unknown:{temp_id}"
        if not self._should_save(key):
            return None
        folder = self.unknown_dir / temp_id
        return self.save_face_image(folder, frame, prefix="pass")

    def capture_attendance(self, student_name: str, frame) -> Optional[str]:
        key = f"attendance:{student_name}"
        if not self._should_save(key):
            return None
        folder = self.attendance_dir / self.safe_folder_name(student_name)
        return self.save_face_image(folder, frame, prefix="attendance")

    def register_manual(
        self,
        name: str,
        frame,
        is_known_student: bool,
    ) -> Tuple[str, Path]:
        """Manual registration from GUI dialog."""
        folder_name = self.safe_folder_name(name)
        if is_known_student:
            folder = self.known_dir / folder_name
        else:
            temp_id = self._next_temp_id()
            folder = self.unknown_dir / temp_id
            folder_name = temp_id
        folder.mkdir(parents=True, exist_ok=True)
        path = self.save_face_image(folder, frame, prefix="register")
        return str(path), folder

    def clear_session(self) -> None:
        self._session_unknown.clear()
