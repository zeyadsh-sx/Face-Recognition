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
import sys
from pathlib import Path
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database_core_mysql import MySQLAttendanceDatabase
from core.features_ai_advanced import (
    EmotionDetector,
    UnknownFaceAlert,
    AdvancedAttendanceReporter,
)
from core.face_capture_manager import FaceCaptureManager
from core.paths import ensure_data_dirs
from core.attendance_service import AttendanceService
from gui.attendance_ui import AttendanceUI

class SimpleMySQLAttendanceGUI:
    def __init__(self, db_config=None):
        # Database connection
        if db_config:
            self.db = MySQLAttendanceDatabase(**db_config)
        else:
            self.db = self.setup_database_connection()
        
        if not self.db:
            messagebox.showerror("Database Error", "Could not connect to MySQL database")
            return
        
        # Initialize variables
        self.camera_running = False
        self.video_capture = None
        self.known_face_encodings = []
        self.known_face_names = []
        self.today_attendance = {}
        self.registered_image_tk = None
        self.flip_camera = False

        ensure_data_dirs()
        self.face_capture = FaceCaptureManager(save_cooldown=3.0)

        self.emotion_detector = EmotionDetector()
        self.unknown_face_alert = UnknownFaceAlert(self.db)
        self.advanced_reporter = AdvancedAttendanceReporter(self.db)
        self.attendance_service = AttendanceService(self.db)
        self.setup_simple_gui()
        self.attendance_ui = AttendanceUI(
            self.root,
            self.db,
            self.attendance_service,
            on_students_changed=self.load_known_faces,
        )
        self._setup_extended_buttons()

        self.load_known_faces()
        self.load_attendance_data()
    
    def setup_database_connection(self):
        """Setup MySQL database connection with default XAMPP settings"""
        try:
            self.db = MySQLAttendanceDatabase(
                host='localhost',
                user='root',
                password='',
                database='attendance_system',
                port=3306
            )
            print("MySQL connection successful!")
            return self.db
        except Exception as e:
            print(f"Connection failed: {e}")
            return None
    
    def setup_simple_gui(self):
        """Setup simple GUI without complex geometry"""
        try:
            self.root = tk.Tk()
            self.root.title("نظام حضور وغياب — التعرف على الوجه")
            self.root.geometry("900x700")
            # Don't set complex geometry that might cause issues
            self.root.configure(bg='#f0f0f0')
        except Exception as e:
            print(f"GUI setup error: {e}")
            return
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="نظام حضور وغياب الطلاب",
            font=('Arial', 16, 'bold'),
        )
        title_label.pack(pady=8)

        row1 = ttk.Frame(main_frame)
        row1.pack(pady=6)
        self.start_btn = ttk.Button(row1, text="تشغيل الكاميرا", command=self.start_camera)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        self.stop_btn = ttk.Button(row1, text="إيقاف", command=self.stop_camera, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=4)
        self.flip_btn = ttk.Button(row1, text="عكس الكاميرا", command=self.toggle_flip_camera)
        self.flip_btn.pack(side=tk.LEFT, padx=4)
        ttk.Button(row1, text="تسجيل طالب", command=self.register_student_simple).pack(side=tk.LEFT, padx=4)
        ttk.Button(row1, text="تسجيل (بيانات كاملة)", command=self._register_full).pack(side=tk.LEFT, padx=4)

        self.main_frame = main_frame

        if not FACE_RECOGNITION_AVAILABLE:
            self.status_label = ttk.Label(main_frame, text="Face recognition unavailable; basic registration enabled.", 
                                        font=('Arial', 12), foreground='orange')
        else:
            self.status_label = ttk.Label(main_frame, text="Ready", 
                                        font=('Arial', 12))
        self.status_label.pack(pady=10)
        
        # Video frame
        self.video_frame = ttk.Label(main_frame, text="Camera will appear here")
        self.video_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Image preview for registration
        self.image_label = ttk.Label(main_frame, text="Selected student image will appear here", anchor='center')
        self.image_label.pack(pady=10, fill=tk.BOTH, expand=True)

    def _setup_extended_buttons(self):
        row2 = ttk.Frame(self.main_frame)
        row2.pack(pady=6)
        ttk.Button(row2, text="بدء/إنهاء محاضرة", command=self.attendance_ui.open_lecture_session).pack(side=tk.LEFT, padx=4)
        ttk.Button(row2, text="تعديل يدوي", command=self.attendance_ui.open_manual_edit).pack(side=tk.LEFT, padx=4)
        ttk.Button(row2, text="تصدير PDF", command=self.attendance_ui._quick_export_pdf).pack(side=tk.LEFT, padx=4)
        ttk.Button(row2, text="إرسال إيميل", command=self.attendance_ui.send_email_report_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(row2, text="إعدادات البريد", command=self.attendance_ui.open_email_settings).pack(side=tk.LEFT, padx=4)
        ttk.Button(row2, text="عرض الحضور", command=self.show_attendance).pack(side=tk.LEFT, padx=4)

    def _register_full(self):
        self.attendance_ui.open_register_full(self._capture_for_registration)

    def _capture_for_registration(self, name: str):
        if not self.camera_running or not self.video_capture:
            messagebox.showerror("خطأ", "شغّل الكاميرا أولاً")
            return None, None, None
        ret, frame = self.video_capture.read()
        if not ret:
            return None, None, None
        if self.flip_camera:
            frame = cv2.flip(frame, 1)
        path, _ = self.face_capture.register_manual(name, frame, is_known=True)
        enc = None
        if FACE_RECOGNITION_AVAILABLE:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locs = face_recognition.face_locations(rgb)
            if locs:
                enc = face_recognition.face_encodings(rgb, locs)[0]
        return frame, enc, path

    def load_known_faces(self):
        """Load known face encodings from database"""
        try:
            students = self.db.get_all_students_v2() if hasattr(self.db, "get_all_students_v2") else self.db.get_all_students()
            known_face_encodings = []
            known_face_names = []
            
            for student in students:
                if student.get('face_encoding') is not None:
                    known_face_encodings.append(student['face_encoding'])
                    known_face_names.append(student['name'])
            
            self.known_face_encodings = known_face_encodings
            self.known_face_names = known_face_names
            print(f"Loaded {len(known_face_names)} known faces from database")
            
        except Exception as e:
            print(f"Error loading known faces: {e}")
            self.known_face_encodings = []
            self.known_face_names = []

    def load_attendance_data(self):
        """Load today's attendance from database"""
        try:
            today = date.today().isoformat()
            if hasattr(self.db, "get_attendance_with_emotions_v2"):
                attendance_records = self.db.get_attendance_with_emotions_v2(today)
            else:
                attendance_records = self.db.get_attendance_with_emotions(today)
            
            self.today_attendance = {}
            for record in attendance_records:
                self.today_attendance[record['name']] = {
                    'time': str(record.get('check_in_time') or record.get('time', '')),
                    'emotion': record.get('emotion', 'N/A'),
                    'status': record.get('attendance_status', 'present'),
                    'is_real_face': record.get('is_real_face', False),
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
            # Try multiple backends for stability on Windows
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]:
                if backend is not None:
                    self.video_capture = cv2.VideoCapture(0, backend)
                else:
                    self.video_capture = cv2.VideoCapture(0)
                
                if self.video_capture.isOpened():
                    break
                    
            if not self.video_capture.isOpened():
                raise Exception("Could not open camera with any backend")
            
            self.face_capture.clear_session()
            self.camera_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="الكاميرا تعمل — التسجيل التلقائي للمارة...")
            
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
        self.face_capture.clear_session()
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="Camera stopped")
        self.video_frame.config(text="Camera stopped")

        if CV2_AVAILABLE:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
    
    def toggle_flip_camera(self):
        """Toggle camera flip"""
        self.flip_camera = not self.flip_camera
        status = "ON" if self.flip_camera else "OFF"
        self.status_label.config(text=f"Camera flip: {status}")
        print(f"Camera flip toggled: {status}")
    
    def camera_loop(self):
        """Camera processing loop"""
        while self.camera_running:
            if not CV2_AVAILABLE or not self.video_capture:
                break

            ret, frame = self.video_capture.read()
            if not ret:
                continue
            
            # Flip camera if enabled
            if self.flip_camera:
                frame = cv2.flip(frame, 1)  # 1 = flip horizontally
                
            # Convert color space
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if FACE_RECOGNITION_AVAILABLE and NUMPY_AVAILABLE:
                # Find faces and encodings
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    face_crop = frame[
                        max(0, top):bottom,
                        max(0, left):right,
                    ]
                    known_name = self.face_capture.match_known(
                        face_encoding,
                        self.known_face_encodings,
                        self.known_face_names,
                    )

                    if known_name:
                        if face_crop.size > 0:
                            emotion_result = self.emotion_detector.detect_emotion(face_crop)
                            emotion = emotion_result.get('emotion', 'neutral')
                        else:
                            emotion = 'neutral'

                        img_path = self.face_capture.capture_known(
                            known_name, face_crop if face_crop.size else frame
                        )
                        self.face_capture.capture_attendance(
                            known_name, face_crop if face_crop.size else frame
                        )
                        ok, msg, info = self.attendance_service.process_face_sighting(
                            known_name,
                            face_crop if face_crop.size else frame,
                            frame,
                            emotion=emotion,
                            image_path=img_path,
                        )
                        if ok:
                            self._update_today_cache(known_name, info.get("status", "present"), emotion)
                            status_ar = {"present": "حاضر", "late": "متأخر"}.get(
                                info.get("status", "present"), "حاضر"
                            )
                            display_text = f"{known_name} [{status_ar}]"
                            color = (0, 255, 0) if info.get("status") != "late" else (0, 200, 255)
                            text_color = (0, 0, 0)
                        elif msg == "spoofing_rejected":
                            display_text = "تحذير: وجه وهمي"
                            color = (0, 0, 255)
                            text_color = (255, 255, 255)
                        elif msg == "mask_required":
                            display_text = f"{known_name} [كمامة]"
                            color = (0, 0, 255)
                            text_color = (255, 255, 255)
                        else:
                            display_text = f"{known_name} [؟]"
                            color = (128, 128, 128)
                            text_color = (255, 255, 255)
                    else:
                        temp_id, is_new_unknown = self.face_capture.match_or_register_unknown(
                            face_encoding
                        )
                        image_path = self.face_capture.capture_unknown(
                            temp_id,
                            face_crop if face_crop.size else frame,
                        )
                        if is_new_unknown and image_path:
                            try:
                                self.db.add_unknown_face(
                                    image_path,
                                    face_encoding,
                                    notes=f"auto_capture:{temp_id}",
                                )
                            except Exception as db_err:
                                print(f"Unknown face DB log error: {db_err}")

                        display_text = temp_id
                        color = (0, 165, 255)
                        text_color = (0, 0, 0)

                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    (text_width, _), _ = cv2.getTextSize(
                        display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
                    )
                    cv2.rectangle(
                        frame,
                        (left, top - 25),
                        (left + text_width, top),
                        color,
                        cv2.FILLED,
                    )
                    cv2.putText(
                        frame,
                        display_text,
                        (left, top - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        text_color,
                        2,
                    )
            elif CV2_AVAILABLE:
                # Fallback - basic face detection when no face encodings available
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
    
    def _update_today_cache(self, name: str, status: str, emotion: str) -> None:
        self.today_attendance[name] = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "emotion": emotion,
            "status": status,
            "is_real_face": True,
        }

    
    def register_student_simple(self):
        """Simple student registration from camera"""
        try:
            if not self.camera_running or self.video_capture is None:
                messagebox.showerror("Error", "Please start the camera first to capture the student's face.")
                return
                
            # Ask for student name
            name = simpledialog.askstring("Register Student", "Enter student name:")
            if not name:
                return
            
            # Capture frame from running camera
            ret, frame = self.video_capture.read()
            if not ret:
                messagebox.showerror("Error", "Failed to capture image from camera.")
                return
                
            if self.flip_camera:
                frame = cv2.flip(frame, 1)

            image_path, folder = self.face_capture.register_manual(name, frame, is_known=True)
            folder_label = "known_faces"
            messagebox.showinfo(
                "معلومة النظام",
                f"تم الحفظ في {folder_label}/{folder.name}",
            )
            
            # Process for UI preview
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            pil_image = pil_image.resize((320, 240), Image.LANCZOS)
            self.registered_image_tk = ImageTk.PhotoImage(pil_image)
            self.image_label.config(image=self.registered_image_tk, text="")
            self.image_label.image = self.registered_image_tk

            face_encoding = None
            if FACE_RECOGNITION_AVAILABLE:
                # Extract face encoding directly from the captured frame
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if not face_locations:
                    messagebox.showerror("Error", "No face found in camera view. Please try again.")
                    try:
                        os.remove(image_path)
                    except:
                        pass
                    return
                
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                face_encoding = face_encodings[0]
            else:
                # Allow registration without face recognition
                messagebox.showinfo("Info", "Face recognition not available. Registering student without face data.")
            
            # Add to database
            student_id = self.db.add_student_with_profile(
                name, face_encoding, image_path
            ) if hasattr(self.db, "add_student_with_profile") else self.db.add_student(
                name, face_encoding, image_path
            )
            
            if student_id:
                messagebox.showinfo("Success", f"Student {name} registered successfully!")
                self.load_known_faces()
            else:
                messagebox.showerror("Error", "Failed to register student")
                
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")
    
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
            
            board = self.attendance_service.get_live_board()
            text_widget.insert(tk.END, f"ملخص: {board['totals']}\n\n")
            if self.today_attendance:
                for name, info in self.today_attendance.items():
                    text_widget.insert(tk.END, f"- {name} [{info.get('status','')}]\n")
                    text_widget.insert(tk.END, f"   Time: {info['time']}\n")
                    text_widget.insert(tk.END, f"   Emotion: {info['emotion']}\n")
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

def main(db_config=None):
    print("Starting Simple MySQL GUI...")
    app = SimpleMySQLAttendanceGUI(db_config=db_config)
    if hasattr(app, 'root') and app.root:
        app.run()


if __name__ == "__main__":
    try:
        from core.mysql_config import (
            MYSQL_DATABASE,
            MYSQL_HOST,
            MYSQL_PASSWORD,
            MYSQL_PORT,
            MYSQL_USER,
        )

        main(
            {
                'host': MYSQL_HOST,
                'user': MYSQL_USER,
                'password': MYSQL_PASSWORD,
                'database': MYSQL_DATABASE,
                'port': MYSQL_PORT,
            }
        )
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {e}")
