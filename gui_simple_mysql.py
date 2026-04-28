#!/usr/bin/env python3
"""
Simple MySQL GUI for Face Recognition Attendance System
Minimal version without complex geometry issues
"""

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

import os
import pickle
import json
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import shutil
import csv
import threading
import time
from database_core_mysql import MySQLAttendanceDatabase
from services.local_database import SQLiteAttendanceDatabase
from services.offline_sync import OfflineSyncService
from services.export_service import ExportService
from services.backup_service import BackupService
from features_ai_advanced import (
    AntiSpoofing,
    EmotionDetector,
    UnknownFaceAlert,
    LectureSystem,
    AdvancedAttendanceReporter,
    MultiFaceAttendanceSystem
)

class SimpleMySQLAttendanceGUI:
    def __init__(self, db_config=None):
        self.mysql_config = db_config or {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'attendance_system',
            'port': 3306
        }
        self.offline_mode = False
        self.local_db = None
        self.sync_service = None
        self.last_unknown_alert_time = None

        self.db = self._connect_database(self.mysql_config)
        if not self.db:
            messagebox.showerror("Database Error", "Could not connect to MySQL database or initialize offline storage")
            return
        
        # Initialize variables
        self.camera_running = False
        self.video_capture = None
        self.known_face_encodings = []
        self.known_face_names = []
        self.today_attendance = {}
        self.registered_image_tk = None
        self.cameras = []
        self.selected_camera_id = None
        self.selected_camera_source = None

        # Advanced features
        self.anti_spoofing = AntiSpoofing()
        self.emotion_detector = EmotionDetector()
        self.unknown_face_alert = UnknownFaceAlert(alert_callback=self.on_unknown_face_detected)
        self.lecture_system = None  # Disable lecture system for simplicity
        self.advanced_reporter = AdvancedAttendanceReporter(self.db)
        self.multi_face_system = MultiFaceAttendanceSystem(self.db, lecture_id='default_lecture', tolerance=0.55, exit_timeout=8)
        self.export_service = ExportService()
        self.backup_service = BackupService()
        self.offline_db_file = "offline_attendance.db"
        self.backup_schedule_hours = 24
        self.export_dir = "exports"
        self.backup_service.start_auto_backup(self.offline_db_file, interval_hours=self.backup_schedule_hours)
        
        # Directories
        self.known_faces_dir = "known_faces"
        self.attendance_images_dir = "attendance_images"
        self.unknown_faces_dir = "unknown_faces"
        
        # Create directories
        os.makedirs(self.known_faces_dir, exist_ok=True)
        os.makedirs(self.attendance_images_dir, exist_ok=True)
        os.makedirs(self.unknown_faces_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Setup GUI
        self.setup_simple_gui()
        
        # Load data
        self.load_known_faces()
        self.load_attendance_data()
    
    def setup_database_connection(self):
        """Setup MySQL database connection with default XAMPP settings"""
        return self._connect_database(self.mysql_config)

    def _connect_database(self, config):
        try:
            db = MySQLAttendanceDatabase(**config)
            print("MySQL connection successful!")
            return db
        except Exception as e:
            print(f"MySQL connection failed, switching to offline SQLite: {e}")
            self._set_offline_mode(reason=str(e))
            return self.local_db

    def _set_offline_mode(self, reason: str = None):
        if self.offline_mode and self.local_db:
            return
        self.offline_mode = True
        self.local_db = self.local_db or SQLiteAttendanceDatabase()
        self.db = self.local_db
        self.sync_service = self.sync_service or OfflineSyncService(self.local_db, self.mysql_config)
        self._start_sync_loop()
        self._update_status_label("Offline mode active. Data is stored locally until connection is restored.")
        if reason:
            print(f"Offline mode enabled: {reason}")

    def _start_sync_loop(self):
        if not self.sync_service:
            return
        sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        sync_thread.start()

    def _sync_loop(self):
        while self.offline_mode:
            result = self.sync_service.sync()
            status = "Offline mode active. Waiting for connection..."
            if result.get('status') == 'success' and result.get('synced', 0) > 0:
                status = f"Offline data synced: {result['synced']} records."
                if result.get('pending', 0) == 0:
                    try:
                        self.db = MySQLAttendanceDatabase(**self.mysql_config)
                        self.offline_mode = False
                        status = "Online sync restored."
                    except Exception as e:
                        status = f"Sync completed, but MySQL reconnect failed: {e}"
            elif result.get('status') == 'partial':
                status = f"Partial sync: {result.get('synced', 0)} synced, {result.get('pending', 0)} pending."
            self._update_status_label(status)
            time.sleep(30)

    def _update_status_label(self, text: str):
        if hasattr(self, 'status_label'):
            try:
                self.root.after(0, lambda: self.status_label.config(text=text))
            except Exception:
                pass

    def setup_simple_gui(self):
        """Setup simple GUI without complex geometry"""
        try:
            self.root = tk.Tk()
            self.root.title("Simple MySQL Attendance System")
            # Don't set complex geometry that might cause issues
            self.root.configure(bg='#f0f0f0')
        except Exception as e:
            print(f"GUI setup error: {e}")
            return
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Simple MySQL Face Recognition", 
                                font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # Start Camera button
        self.start_btn = ttk.Button(button_frame, text="📹 Start Camera", 
                                   command=self.start_camera)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop Camera button
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Stop Camera", 
                                  command=self.stop_camera, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Register Student button
        self.register_btn = ttk.Button(button_frame, text="👤 Register Student", 
                                    command=self.register_student_simple)
        self.register_btn.pack(side=tk.LEFT, padx=5)

        # Camera selector and add button
        camera_frame = ttk.Frame(main_frame)
        camera_frame.pack(pady=10, fill=tk.X)

        ttk.Label(camera_frame, text="Select Camera:").pack(side=tk.LEFT, padx=(0, 5))
        self.camera_selector = ttk.Combobox(camera_frame, state='readonly', width=40)
        self.camera_selector.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.camera_selector.bind("<<ComboboxSelected>>", self.on_camera_selected)

        self.add_camera_btn = ttk.Button(camera_frame, text="➕ Add Camera", command=self.add_camera_dialog)
        self.add_camera_btn.pack(side=tk.LEFT, padx=5)
        
        if not FACE_RECOGNITION_AVAILABLE:
            self.register_btn.config(state='normal')  # Allow registration even without face recognition

        self.load_camera_sources()
        
        # View Attendance button
        self.attendance_btn = ttk.Button(button_frame, text="📊 View Attendance", 
                                      command=self.show_attendance)
        self.attendance_btn.pack(side=tk.LEFT, padx=5)

        # Export report button
        self.export_btn = ttk.Button(button_frame, text="📤 Export Report",
                                      command=self.export_report_dialog)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        # Backup buttons
        self.backup_btn = ttk.Button(button_frame, text="💾 Backup Now", command=self.backup_now)
        self.backup_btn.pack(side=tk.LEFT, padx=5)
        self.restore_btn = ttk.Button(button_frame, text="♻️ Restore Backup", command=self.restore_backup_dialog)
        self.restore_btn.pack(side=tk.LEFT, padx=5)
        self.schedule_btn = ttk.Button(button_frame, text="⏰ Backup Schedule", command=self.configure_backup_schedule)
        self.schedule_btn.pack(side=tk.LEFT, padx=5)
        
        if self.offline_mode:
            status_text = "Offline mode active. Data stored locally and will sync when online."
        elif not FACE_RECOGNITION_AVAILABLE:
            status_text = "Face recognition unavailable; basic registration enabled."
        else:
            status_text = "Ready"

        self.status_label = ttk.Label(main_frame, text=status_text, 
                                     font=('Arial', 12), foreground='orange' if self.offline_mode else 'black')
        self.status_label.pack(pady=10)
        
        # Video frame
        self.video_frame = ttk.Label(main_frame, text="Camera will appear here")
        self.video_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Image preview for registration
        self.image_label = ttk.Label(main_frame, text="Selected student image will appear here", anchor='center')
        self.image_label.pack(pady=10, fill=tk.BOTH, expand=True)
    
    def load_known_faces(self):
        """Load known face encodings from database"""
        try:
            students = self.db.get_all_students()
            known_face_encodings = []
            known_face_names = []
            
            for student in students:
                if student.get('face_encoding') is not None:
                    known_face_encodings.append(student['face_encoding'])
                    known_face_names.append(student['name'])
            
            self.known_face_encodings = known_face_encodings
            self.known_face_names = known_face_names
            self.multi_face_system.load_known_students()
            print(f"Loaded {len(known_face_names)} known faces from database")
            
        except Exception as e:
            print(f"Error loading known faces: {e}")
            self.known_face_encodings = []
            self.known_face_names = []

    def on_unknown_face_detected(self, unknown_face_info):
        """Handle realtime notification for unknown face detection"""
        try:
            if hasattr(self.db, 'add_unknown_face'):
                self.db.add_unknown_face(unknown_face_info['image_path'])
            if hasattr(self.db, 'create_alert'):
                self.db.create_alert('unknown_face', f"Unknown face detected at {unknown_face_info['timestamp']}")
        except Exception as e:
            print(f"Failed to persist unknown face alert: {e}")

        def notify():
            self.status_label.config(text="Unknown face detected! Saved for review.")
            messagebox.showwarning(
                "Unknown Face Detected",
                "A face was detected that does not match any registered student. The image has been saved for review."
            )

        if hasattr(self, 'root'):
            try:
                self.root.after(0, notify)
            except Exception:
                notify()

    def load_camera_sources(self):
        """Load available cameras for selection"""
        try:
            self.cameras = self.db.get_all_cameras() if self.db else []
            camera_names = [f"{cam['id']}: {cam['name']} ({cam['source']})" for cam in self.cameras]
            self.camera_selector['values'] = camera_names
            if camera_names:
                self.camera_selector.current(0)
                self.on_camera_selected()
        except Exception as e:
            print(f"Error loading camera sources: {e}")

    def on_camera_selected(self, event=None):
        try:
            selection = self.camera_selector.get()
            if not selection:
                self.selected_camera_id = None
                self.selected_camera_source = None
                return

            camera_id = int(selection.split(':', 1)[0])
            camera = next((c for c in self.cameras if c['id'] == camera_id), None)
            if camera:
                self.selected_camera_id = camera['id']
                self.selected_camera_source = camera['source']
        except Exception as e:
            print(f"Error selecting camera: {e}")
            self.selected_camera_id = None
            self.selected_camera_source = None

    def add_camera_dialog(self):
        """Add a new camera source to the system"""
        try:
            name = simpledialog.askstring("Add Camera", "Enter camera name:")
            if not name:
                return

            source = simpledialog.askstring("Add Camera", "Enter camera source (0 for default webcam, RTSP/HTTP URL or device path):")
            if not source:
                return

            location = simpledialog.askstring("Add Camera", "Enter camera location (optional):")
            ip_address = simpledialog.askstring("Add Camera", "Enter camera IP address (optional):")

            camera_id = self.db.add_camera(name, source, location, ip_address)
            if camera_id:
                messagebox.showinfo("Success", f"Camera '{name}' added successfully.")
                self.load_camera_sources()
            else:
                messagebox.showerror("Error", "Failed to add camera.")
        except Exception as e:
            messagebox.showerror("Error", f"Unable to add camera: {e}")

    def load_attendance_data(self):
        """Load today's attendance from database"""
        try:
            today = date.today().isoformat()
            attendance_records = self.db.get_attendance_with_emotions(today)
            
            self.today_attendance = {}
            for record in attendance_records:
                self.today_attendance[record['name']] = {
                    'time': record['time'],
                    'emotion': record.get('emotion', 'N/A'),
                    'is_real_face': record.get('is_real_face', False)
                }
            
            print(f"Loaded {len(attendance_records)} attendance records for today")
            
        except Exception as e:
            print(f"Error loading attendance: {e}")
            self.today_attendance = {}
    
    def start_camera(self):
        """Start camera for face recognition"""
        if not CV2_AVAILABLE:
            messagebox.showerror("Camera Error", "OpenCV is not available. Please install opencv-python to use the camera.")
            return

        try:
            source = self.selected_camera_source if self.selected_camera_source else '0'
            try:
                source_index = int(source)
            except ValueError:
                source_index = source

            self.video_capture = cv2.VideoCapture(source_index)
            if not self.video_capture.isOpened():
                raise Exception("Could not open camera source: " + str(source))
            
            self.camera_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="Camera running...")
            
            # Start camera thread
            camera_thread = threading.Thread(target=self.camera_loop)
            camera_thread.daemon = True
            camera_thread.start()
            
        except Exception as e:
            messagebox.showerror("Camera Error", f"Could not start camera: {e}")
    
    def stop_camera(self):
        """Stop camera"""
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        self.camera_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="Camera stopped")
        self.video_frame.config(text="Camera stopped")

        if CV2_AVAILABLE:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
    
    def camera_loop(self):
        """Camera processing loop"""
        while self.camera_running:
            if not CV2_AVAILABLE or not self.video_capture:
                break

            ret, frame = self.video_capture.read()
            if not ret:
                continue
                
            # Convert color space
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if CV2_AVAILABLE:
                recognized_faces, tracked_faces = self.multi_face_system.process_frame(frame)

                for face in recognized_faces:
                    if face.get('student_id') is None:
                        now = datetime.now()
                        if not self.last_unknown_alert_time or (now - self.last_unknown_alert_time).total_seconds() > 10:
                            self.last_unknown_alert_time = now
                            x, y, w, h = face['bounding_box']
                            face_region = frame[y:y+h, x:x+w]
                            self.unknown_face_alert.handle_unknown_face(face_region, frame, now)
                    else:
                        name = face.get('name', 'Unknown')
                        first_seen = name not in self.today_attendance
                        self.today_attendance[name] = {
                            'time': datetime.now().time().strftime("%H:%M:%S"),
                            'emotion': face.get('emotion_data', {}).get('emotion', 'neutral'),
                            'is_real_face': True
                        }
                        if first_seen:
                            self.mark_attendance_simple(name)

                frame = self.multi_face_system.annotate_frame(frame, recognized_faces, tracked_faces)
            else:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, "Face Detected (No Recognition)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow('Face Recognition', frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    def mark_attendance_simple(self, name):
        """Mark attendance in database"""
        try:
            student = self.db.get_student_by_name(name)
            if not student:
                print(f"Error marking attendance: student '{name}' not found")
                return

            now = datetime.now()
            date_str = now.date().isoformat()
            time_str = now.time().strftime("%H:%M:%S")

            success, message = self.db.mark_attendance_advanced(
                student_id=student['id'],
                date_str=date_str,
                time_str=time_str,
                emotion='neutral',
                is_real_face=True,
                camera_id=self.selected_camera_id
            )

            if not success and not self.offline_mode and message.startswith("Database error"):
                self._set_offline_mode(reason=message)
                success, message = self.db.mark_attendance_advanced(
                    student_id=student['id'],
                    date_str=date_str,
                    time_str=time_str,
                    emotion='neutral',
                    is_real_face=True,
                    camera_id=self.selected_camera_id
                )

            if success:
                self.today_attendance[name] = {
                    'time': time_str,
                    'emotion': 'neutral',
                    'is_real_face': True
                }
            else:
                print(f"Error marking attendance: {message}")

        except Exception as e:
            print(f"Error marking attendance: {e}")
            if not self.offline_mode:
                self._set_offline_mode(reason=str(e))
    
    def register_student_simple(self):
        """Simple student registration"""
        try:
            # Ask for student name
            name = simpledialog.askstring("Register Student", "Enter student name:")
            if not name:
                return
            
            # Ask for image file
            image_path = filedialog.askopenfilename(
                title="Select student image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png")]
            )
            
            if not image_path:
                return
            
            # Show selected image preview even if face recognition is not available
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((320, 240), Image.LANCZOS)
            self.registered_image_tk = ImageTk.PhotoImage(pil_image)
            self.image_label.config(image=self.registered_image_tk, text="")
            self.image_label.image = self.registered_image_tk

            face_encoding = None
            if FACE_RECOGNITION_AVAILABLE:
                # Load and process image
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)
                
                if not face_encodings:
                    messagebox.showerror("Error", "No face found in image")
                    return
                
                face_encoding = face_encodings[0]
            else:
                # Allow registration without face recognition
                messagebox.showinfo("Info", "Face recognition not available. Registering student without face data.")
            
            # Add to database
            student_id = self.db.add_student(name, face_encoding, image_path)
            
            if not student_id and not self.offline_mode:
                self._set_offline_mode(reason="MySQL write failed during registration")
                student_id = self.db.add_student(name, face_encoding, image_path)

            if student_id:
                messagebox.showinfo("Success", f"Student {name} registered successfully!")
                self.load_known_faces()
                self.multi_face_system.load_known_students()
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")
            if not self.offline_mode:
                self._set_offline_mode(reason=str(e))
    
    def export_report_dialog(self):
        """Export attendance report for a date range."""
        try:
            start_date = simpledialog.askstring("Export Report", "Start date (YYYY-MM-DD):", initialvalue=date.today().isoformat())
            if not start_date:
                return

            end_date = simpledialog.askstring("Export Report", "End date (YYYY-MM-DD):", initialvalue=date.today().isoformat())
            if not end_date:
                return

            format_choice = simpledialog.askstring(
                "Export Format",
                "Choose export format (csv, excel, pdf, json):",
                initialvalue="csv"
            )
            if not format_choice:
                return

            format_choice = format_choice.strip().lower()
            if format_choice not in ('csv', 'excel', 'pdf', 'json'):
                messagebox.showerror("Export Error", "Invalid export format selected.")
                return

            attendance_records = self.db.get_attendance_by_date_range(start_date, end_date)
            if not attendance_records:
                messagebox.showinfo("No Records", "No attendance records found for the selected period.")
                return

            extension = 'csv' if format_choice == 'csv' else 'xlsx' if format_choice == 'excel' else 'pdf' if format_choice == 'pdf' else 'json'
            filename = os.path.join(self.export_dir, f"attendance_{start_date}_{end_date}.{extension}")

            if format_choice == 'csv':
                success, result = self.export_service.export_to_csv(attendance_records, filename)
            elif format_choice == 'excel':
                success, result = self.export_service.export_to_excel(attendance_records, filename)
            elif format_choice == 'pdf':
                success, result = self.export_service.export_to_pdf(attendance_records, filename, title=f"Attendance Report {start_date} to {end_date}")
            else:
                success, result = self.export_service.export_to_json(attendance_records, filename)

            if success:
                messagebox.showinfo("Export Complete", f"Report saved to: {result}")
            else:
                messagebox.showerror("Export Failed", f"Could not export report: {result}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report: {e}")

    def backup_now(self):
        try:
            backup_path = self.offline_db_file
            success, result = self.backup_service.backup_database_file(backup_path)
            if success:
                messagebox.showinfo("Backup Complete", f"Backup saved: {result}")
            else:
                messagebox.showerror("Backup Failed", f"Could not create backup: {result}")
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Could not create backup: {e}")

    def restore_backup_dialog(self):
        try:
            backup_file = filedialog.askopenfilename(
                title="Select backup to restore",
                initialdir=self.backup_service.backup_dir,
                filetypes=[("SQLite Backup Files", "*.db"), ("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not backup_file:
                return

            restore_path = filedialog.asksaveasfilename(
                title="Restore backup to",
                initialdir=os.getcwd(),
                initialfile=os.path.basename(self.offline_db_file),
                defaultextension=os.path.splitext(backup_file)[1] or ".db",
                filetypes=[("SQLite Backup Files", "*.db"), ("All files", "*.*")]
            )
            if not restore_path:
                return

            success, result = self.backup_service.restore_backup(backup_file, restore_path)
            if success:
                messagebox.showinfo("Restore Complete", f"Backup restored to: {result}\nPlease restart the app if needed.")
            else:
                messagebox.showerror("Restore Failed", f"Could not restore backup: {result}")
        except Exception as e:
            messagebox.showerror("Restore Failed", f"Could not restore backup: {e}")

    def configure_backup_schedule(self):
        try:
            interval_hours = simpledialog.askinteger(
                "Backup Schedule",
                "Auto-backup interval (hours):",
                initialvalue=self.backup_schedule_hours,
                minvalue=1,
                maxvalue=168
            )
            if interval_hours is None:
                return

            self.backup_schedule_hours = interval_hours
            self.backup_service.stop_auto_backup()
            success, result = self.backup_service.start_auto_backup(self.offline_db_file, interval_hours=self.backup_schedule_hours)
            if success:
                messagebox.showinfo("Schedule Updated", result)
            else:
                messagebox.showerror("Schedule Error", result)
        except Exception as e:
            messagebox.showerror("Schedule Error", f"Could not set backup schedule: {e}")

    def show_attendance(self):
        """Show attendance in a simple window"""
        try:
            # Create new window
            attendance_window = tk.Toplevel(self.root)
            attendance_window.title("Today's Attendance")
            attendance_window.geometry("600x400")
            
            # Create text widget
            text_widget = tk.Text(attendance_window, wrap=tk.WORD, height=15)
            text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(text_widget)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_widget.yview)
            
            # Display attendance
            text_widget.insert(tk.END, f"Today's Attendance ({date.today().isoformat()})\n")
            text_widget.insert(tk.END, "=" * 40 + "\n\n")
            
            if self.today_attendance:
                for name, info in self.today_attendance.items():
                    text_widget.insert(tk.END, f"👤 {name}\n")
                    text_widget.insert(tk.END, f"   🕐 Time: {info['time']}\n")
                    text_widget.insert(tk.END, f"   😊 Emotion: {info['emotion']}\n")
                    text_widget.insert(tk.END, f"   ✅ Real Face: {info['is_real_face']}\n")
                    text_widget.insert(tk.END, "-" * 30 + "\n")
            else:
                text_widget.insert(tk.END, "No attendance records for today\n")
            
            # Close button
            close_btn = ttk.Button(attendance_window, text="Close", 
                                 command=attendance_window.destroy)
            close_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not show attendance: {e}")
    
    def run(self):
        """Run the application"""
        if self.root:
            self.root.mainloop()

if __name__ == "__main__":
    try:
        print("Starting Simple MySQL GUI...")
        app = SimpleMySQLAttendanceGUI()
        if hasattr(app, 'root'):
            print("GUI initialized successfully")
            app.run()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {e}")
