# services/offline_sync.py

import base64
import json
import os
import pickle
from typing import Optional

# from services.local_database import SQLiteAttendanceDatabase


class OfflineSyncService:

    def __init__(self, local_db: SQLiteAttendanceDatabase, mysql_config: Optional[dict] = None):
        self.local_db = local_db
        self.mysql_config = mysql_config or {}
        self.file = "offline_data.json"

    def _build_remote_db(self):
        from database_core_mysql import MySQLAttendanceDatabase

        if not self.mysql_config:
            raise RuntimeError("No MySQL configuration provided for sync")

        return MySQLAttendanceDatabase(**self.mysql_config)

    def save_offline(self, record):
        data = []

        if os.path.exists(self.file):
            with open(self.file, "r") as f:
                data = json.load(f)

        data.append(record)

        with open(self.file, "w") as f:
            json.dump(data, f, indent=2)

    def sync(self) -> dict:
        if not self.mysql_config:
            return {
                'status': 'offline',
                'message': 'No MySQL configuration available for sync'
            }

        try:
            remote_db = self._build_remote_db()
        except Exception as e:
            return {
                'status': 'offline',
                'message': f'Unable to connect to remote MySQL: {e}'
            }

        queue = self.local_db.get_sync_queue()
        synced = 0
        total = len(queue)

        for entry in queue:
            entity = entry['entity']
            payload = json.loads(entry['payload'])
            success = False

            try:
                if entity == 'student':
                    face_encoding = None
                    if payload.get('face_encoding'):
                        face_encoding = pickle.loads(base64.b64decode(payload['face_encoding']))

                    remote_id = remote_db.add_student(
                        payload['name'],
                        face_encoding,
                        payload.get('image_path'),
                        payload.get('notes')
                    )
                    success = bool(remote_id)

                elif entity == 'camera':
                    remote_id = remote_db.add_camera(
                        payload['name'],
                        payload['source'],
                        payload.get('location'),
                        payload.get('ip_address'),
                        payload.get('is_active', True)
                    )
                    success = bool(remote_id)

                elif entity == 'attendance':
                    student = remote_db.get_student_by_name(payload['student_name'])
                    if not student:
                        success = False
                    else:
                        camera_id = None
                        if payload.get('camera_source'):
                            camera = remote_db.get_camera_by_source(payload['camera_source'])
                            if camera:
                                camera_id = camera['id']
                            else:
                                camera_id = remote_db.add_camera(
                                    payload.get('camera_name') or payload['camera_source'],
                                    payload['camera_source'],
                                    payload.get('camera_location'),
                                    payload.get('camera_ip_address')
                                )

                        success, _ = remote_db.mark_attendance_advanced(
                            student_id=student['id'],
                            date_str=payload['date'],
                            time_str=payload['time'],
                            image_path=payload.get('image_path'),
                            emotion=payload.get('emotion'),
                            emotion_confidence=payload.get('emotion_confidence'),
                            spoofing_score=payload.get('spoofing_score'),
                            is_real_face=payload.get('is_real_face', True),
                            camera_id=camera_id,
                            mask_detected=payload.get('mask_detected'),
                            mask_confidence=payload.get('mask_confidence'),
                            mask_violation=payload.get('mask_violation', False),
                            lecture_id=payload.get('lecture_id')
                        )

                elif entity == 'alert':
                    remote_id = remote_db.create_alert(
                        payload['alert_type'],
                        payload['message'],
                        payload.get('student_id')
                    )
                    success = bool(remote_id)

                elif entity == 'unknown_face':
                    remote_id = remote_db.add_unknown_face(
                        payload['image_path'],
                        None,
                        payload.get('notes')
                    )
                    success = bool(remote_id)

                if success:
                    self.local_db.mark_sync_done(entry['id'])
                    synced += 1
            except Exception:
                continue

        return {
            'status': 'success' if synced == total else 'partial',
            'synced': synced,
            'pending': total - synced
        }
