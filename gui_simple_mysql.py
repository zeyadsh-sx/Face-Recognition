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

# Try to import face_recognition, if not available use OpenCV's LBP recognizer
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    # Use OpenCV's LBP face recognizer as fallback
    try:
        if CV2_AVAILABLE:
            face_recognition = None
            # Will use cv2.face.LBPHFaceRecognizer instead
    except:
        pass

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
from features_ai_advanced import AntiSpoofing, EmotionDetector, UnknownFaceAlert, LectureSystem, AdvancedAttendanceReporter, FaceQualityAssessment, FaceClustering

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
        
        # Advanced features
        self.anti_spoofing = AntiSpoofing()
        self.emotion_detector = EmotionDetector()
        self.unknown_face_alert = UnknownFaceAlert(self.db)
        self.lecture_system = None  # Disable lecture system for simplicity
        self.advanced_reporter = AdvancedAttendanceReporter(self.db)
        self.face_quality = FaceQualityAssessment()  # Face Quality Assessment
        self.face_clustering = FaceClustering()  # Face Clustering
        
        # OpenCV face recognizer (fallback when face_recognition not available)
        self.face_recognizer = None
        self.face_label_map = {}  # Maps label ID to student name
        if not FACE_RECOGNITION_AVAILABLE and CV2_AVAILABLE:
            try:
                import cv2.face
                self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
                print("OpenCV face recognizer initialized (fallback mode)")
            except Exception as e:
                print(f"Could not initialize OpenCV face recognizer: {e}")
        
        # Directories
        self.known_faces_dir = "known_faces"
        self.attendance_images_dir = "attendance_images"
        self.unknown_faces_dir = "unknown_faces"
        
        # Create directories
        os.makedirs(self.known_faces_dir, exist_ok=True)
        os.makedirs(self.attendance_images_dir, exist_ok=True)
        os.makedirs(self.unknown_faces_dir, exist_ok=True)
        
        # Setup GUI
        self.setup_simple_gui()
        
        # Load data
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
        
        if not FACE_RECOGNITION_AVAILABLE:
            self.register_btn.config(state='normal')  # Allow registration even without face recognition
        
        # View Attendance button
        self.attendance_btn = ttk.Button(button_frame, text="📊 View Attendance", 
                                command=self.show_attendance)
        self.attendance_btn.pack(side=tk.LEFT, padx=5)
        
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
    
    def load_known_faces(self):
        """Load known face encodings from database"""
        try:
            students = self.db.get_all_students()
            known_face_encodings = []
            known_face_names = []
            
            # For OpenCV face recognizer fallback
            if not FACE_RECOGNITION_AVAILABLE and self.face_recognizer is not None:
                import cv2
                training_images = []
                training_labels = []
                self.face_label_map = {}
                label_counter = 0
            
            for student in students:
                if student.get('face_encoding') is not None:
                    known_face_encodings.append(student['face_encoding'])
                    known_face_names.append(student['name'])
                    
                    # Add to face clustering system
                    if hasattr(student, 'id') and student.get('face_encoding') is not None:
                        self.face_clustering.add_face(
                            face_id=str(student['id']),
                            face_encoding=student['face_encoding'],
                            metadata={
                                'name': student['name'],
                                'image_path': student.get('image_path', '')
                            }
                        )
                    
                    # For OpenCV recognizer - load training images
                    if not FACE_RECOGNITION_AVAILABLE and self.face_recognizer is not None:
                        image_path = student.get('image_path')
                        if image_path and os.path.exists(image_path):
                            try:
                                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                                if img is not None:
                                    training_images.append(img)
                                    training_labels.append(label_counter)
                                    self.face_label_map[label_counter] = student['name']
                                    label_counter += 1
                            except Exception as e:
                                print(f"Error loading image {image_path}: {e}")
            
            # Train OpenCV recognizer if we have training data
            if not FACE_RECOGNITION_AVAILABLE and self.face_recognizer is not None and training_images:
                try:
                    self.face_recognizer.train(training_images, np.array(training_labels))
                    print(f"OpenCV face recognizer trained with {len(training_images)} images")
                except Exception as e:
                    print(f"Error training OpenCV recognizer: {e}")
            
            self.known_face_encodings = known_face_encodings
            self.known_face_names = known_face_names
            
            # Run clustering analysis
            if len(known_face_names) > 1:
                duplicate_groups = self.face_clustering.detect_duplicate_groups()
                if duplicate_groups:
                    print(f"⚠️ Found {len(duplicate_groups)} potential duplicate groups")
            
            print(f"Loaded {len(known_face_names)} known faces from database")
            
        except Exception as e:
            print(f"Error loading known faces: {e}")
            self.known_face_encodings = []
            self.known_face_names = []

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
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                raise Exception("Could not open camera")
            
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
            
            if FACE_RECOGNITION_AVAILABLE and NUMPY_AVAILABLE and self.known_face_encodings:
                # Find faces and encodings
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                # Loop through found faces
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Extract face region for quality assessment
                    face_region = frame[top:bottom, left:right]
                    
                    # Face Quality Assessment - تقييم جودة الصورة
                    quality_result = self.face_quality.assess_quality(face_region, frame, (top, right, bottom, left))
                    
                    # Draw quality indicator on frame
                    frame = self.face_quality.draw_quality_indicator(frame, (top, right, bottom, left), quality_result)
                    
                    # Only proceed if quality is acceptable
                    if not quality_result['is_acceptable']:
                        # Show warning message
                        quality_msg = self.face_quality.get_quality_message(quality_result)
                        cv2.putText(frame, quality_msg[:50], (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                        continue  # Skip this face - quality not acceptable
                    
                    # Compare with known faces
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                    name = "Unknown"
                    
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_face_names[first_match_index]
                        
                        # Mark attendance
                        self.mark_attendance_simple(name)
                    
                    # Draw rectangle and name
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            elif CV2_AVAILABLE:
                # Fallback - use OpenCV face recognizer if available
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                face_cascade = cv2.CascadeClassifier(cascade_path)
                if face_cascade.empty():
                    # Try alternative path
                    cv2_path = os.path.dirname(cv2.__file__)
                    cascade_path = os.path.join(cv2_path, 'data', 'haarcascade_frontalface_default.xml')
                    face_cascade = cv2.CascadeClassifier(cascade_path)
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in faces:
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Try to recognize face using OpenCV recognizer
                    name = "Unknown"
                    if self.face_recognizer is not None:
                        try:
                            face_roi = gray[y:y+h, x:x+w]
                            if face_roi.size > 0:
                                label, confidence = self.face_recognizer.predict(face_roi)
                                if label in self.face_label_map and confidence < 70:
                                    name = self.face_label_map[label]
                                    # Mark attendance
                                    self.mark_attendance_simple(name)
                        except Exception as e:
                            print(f"Face recognition error: {e}")
                    
                    cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
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
                is_real_face=True
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

            # Face Quality Assessment for registration image
            if CV2_AVAILABLE:
                # Load image with OpenCV for quality assessment
                cv_image = cv2.imread(image_path)
                if cv_image is not None:
                    # Get face location if available
                    if FACE_RECOGNITION_AVAILABLE:
                        image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                        face_locations = face_recognition.face_locations(image_rgb)
                        if face_locations:
                            top, right, bottom, left = face_locations[0]
                            face_region = cv_image[top:bottom, left:right]
                            quality_result = self.face_quality.assess_quality(face_region, cv_image, face_locations[0])
                            
                            if not quality_result['is_acceptable']:
                                quality_msg = self.face_quality.get_quality_message(quality_result)
                                messagebox.showwarning("Image Quality Warning", quality_msg)
                                return  # Reject the image

            face_encoding = None
            if FACE_RECOGNITION_AVAILABLE:
                # Load and process image
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)
                
                if not face_encodings:
                    messagebox.showerror("Error", "No face found in image")
                    return
                
                face_encoding = face_encodings[0]
                
                # Face Clustering - Check for duplicates before registration
                temp_clustering = FaceClustering()
                temp_clustering.add_face('temp_new', face_encoding, {'name': name, 'image_path': image_path})
                
                # Compare with existing faces
                for existing_id, existing_encoding in self.face_clustering.face_encodings.items():
                    distance = np.linalg.norm(face_encoding - existing_encoding)
                    if distance < 0.6:  # Similar face found
                        existing_name = self.face_clustering.face_metadata.get(existing_id, {}).get('name', 'Unknown')
                        response = messagebox.askyesno(
                            "Duplicate Detected",
                            f"This face is similar to '{existing_name}' already registered.\n\n"
                            f"Do you want to continue anyway?"
                        )
                        if not response:
                            return
                        break
            elif self.face_recognizer is not None:
                # For OpenCV recognizer, we need grayscale images
                cv_image = cv2.imread(image_path)
                if cv_image is not None:
                    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                    # Save grayscale version to known_faces directory
                    student_image_path = os.path.join(self.known_faces_dir, f"{name}.jpg")
                    cv2.imwrite(student_image_path, gray)
                    image_path = student_image_path
                    messagebox.showinfo("Info", "Student registered with OpenCV face recognizer (fallback mode)")
                else:
                    messagebox.showerror("Error", "Could not process image")
                    return
            else:
                # No face recognition available at all
                messagebox.showinfo("Info", "Face recognition not available. Registering student without face data.")
            
            # Add to database
            student_id = self.db.add_student(name, face_encoding, image_path)
            
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
