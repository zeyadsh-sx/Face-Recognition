# services/backup_service.py

import json
import os
import shutil
import sqlite3
import threading
from datetime import datetime

class BackupService:
    """Backup service with automatic scheduling and restore support."""

    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
        self._stop_event = threading.Event()
        self._auto_backup_thread = None

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def backup_database_file(self, db_path):
        if not os.path.exists(db_path):
            return False, f"Database file not found: {db_path}"

        try:
            timestamp = self._timestamp()
            backup_file = os.path.join(self.backup_dir, f"db_backup_{timestamp}.db")

            if db_path.lower().endswith(('.db', '.sqlite')):
                with sqlite3.connect(db_path) as source_conn:
                    with sqlite3.connect(backup_file) as dest_conn:
                        source_conn.backup(dest_conn)
            else:
                shutil.copy2(db_path, backup_file)

            return True, backup_file
        except Exception as e:
            return False, str(e)

    def list_backups(self, extension=None):
        backups = []
        for filename in os.listdir(self.backup_dir):
            if extension and not filename.lower().endswith(extension.lower()):
                continue
            backups.append(os.path.join(self.backup_dir, filename))
        backups.sort(key=lambda path: os.path.getmtime(path), reverse=True)
        return backups

    def restore_backup(self, backup_file, restore_path=None):
        if not os.path.exists(backup_file):
            return False, f"Backup file not found: {backup_file}"
        restore_path = restore_path or backup_file
        try:
            shutil.copy2(backup_file, restore_path)
            return True, restore_path
        except Exception as e:
            return False, str(e)

    def cleanup_backups(self, keep_latest=10):
        backups = self.list_backups()
        removed = []
        for old_backup in backups[keep_latest:]:
            try:
                os.remove(old_backup)
                removed.append(old_backup)
            except Exception:
                pass
        return removed

    def _auto_backup_loop(self, db_path, interval_seconds):
        while not self._stop_event.wait(interval_seconds):
            success, result = self.backup_database_file(db_path)
            if success:
                print(f"[BackupService] Auto-backup saved: {result}")
            else:
                print(f"[BackupService] Auto-backup failed: {result}")

    def start_auto_backup(self, db_path, interval_hours=24):
        if self._auto_backup_thread and self._auto_backup_thread.is_alive():
            return False, "Auto-backup is already running"
        if not db_path:
            return False, "Database path is required for auto-backup"

        if not os.path.exists(db_path) and db_path.lower().endswith(('.db', '.sqlite')):
            sqlite3.connect(db_path).close()

        interval_seconds = max(60, interval_hours * 3600)
        self._stop_event.clear()
        self._auto_backup_thread = threading.Thread(
            target=self._auto_backup_loop,
            args=(db_path, interval_seconds),
            daemon=True
        )
        self._auto_backup_thread.start()
        return True, f"Auto-backup started every {interval_hours} hour(s)"

    def stop_auto_backup(self):
        self._stop_event.set()
        if self._auto_backup_thread:
            self._auto_backup_thread.join(timeout=1)
        self._auto_backup_thread = None
        return True, "Auto-backup stopped"

    def backup_json(self, data, name="backup"):
        try:
            timestamp = self._timestamp()
            file_path = os.path.join(self.backup_dir, f"{name}_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            return True, file_path
        
        except Exception as e:
            return False, str(e)