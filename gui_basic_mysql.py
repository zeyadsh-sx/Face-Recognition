#!/usr/bin/env python3
"""
Basic MySQL GUI for Face Recognition Attendance System
Minimal version without camera for testing
"""

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    print("✅ face_recognition available!")
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("⚠️ face_recognition not available, using fallback methods")

import cv2
import numpy as np
import os
import pickle
import json
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import shutil
import csv
import threading
import time
from database_core_mysql import MySQLAttendanceDatabase

class BasicMySQLAttendanceGUI:
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
        self.known_face_encodings = []
        self.known_face_names = []
        self.today_attendance = {}
        
        # Directories
        self.known_faces_dir = "known_faces"
        self.attendance_images_dir = "attendance_images"
        self.unknown_faces_dir = "unknown_faces"
        
        # Create directories
        os.makedirs(self.known_faces_dir, exist_ok=True)
        os.makedirs(self.attendance_images_dir, exist_ok=True)
        os.makedirs(self.unknown_faces_dir, exist_ok=True)
        
        # Setup GUI
        self.setup_basic_gui()
        
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
            print("✅ MySQL connection successful!")
            return self.db
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None
    
    def setup_basic_gui(self):
        """Setup basic GUI without camera"""
        try:
            self.root = tk.Tk()
            self.root.title("Basic MySQL Attendance System")
            self.root.configure(bg='#f0f0f0')
        except Exception as e:
            print(f"GUI setup error: {e}")
            return
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Basic MySQL Face Recognition", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        
        # Database status
        db_status = "✅ Connected" if self.db else "❌ Disconnected"
        ttk.Label(status_frame, text=f"MySQL Database: {db_status}").pack(anchor=tk.W, pady=5)
        
        # Students count
        try:
            if self.db:
                students = self.db.get_all_students()
                student_count = len(students)
                ttk.Label(status_frame, text=f"Registered Students: {student_count}").pack(anchor=tk.W, pady=5)
        except:
            ttk.Label(status_frame, text="Registered Students: 0").pack(anchor=tk.W, pady=5)
        
        # Today's attendance count
        try:
            if self.db:
                today = date.today().isoformat()
                attendance_records = self.db.get_attendance_with_emotions(today)
                attendance_count = len(attendance_records)
                ttk.Label(status_frame, text=f"Today's Attendance: {attendance_count}").pack(anchor=tk.W, pady=5)
        except:
            ttk.Label(status_frame, text="Today's Attendance: 0").pack(anchor=tk.W, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # Register Student button
        register_btn = ttk.Button(button_frame, text="👤 Register Student", 
                                   command=self.register_student_basic)
        register_btn.pack(side=tk.LEFT, padx=5)
        
        # Register Student with Camera button
        register_camera_btn = ttk.Button(button_frame, text="📹 Register with Camera", 
                                        command=self.register_student_with_camera)
        register_camera_btn.pack(side=tk.LEFT, padx=5)
        
        # View Attendance button
        attendance_btn = ttk.Button(button_frame, text="📊 View Attendance", 
                                      command=self.show_attendance_basic)
        attendance_btn.pack(side=tk.LEFT, padx=5)
        
        # Test Database button
        test_btn = ttk.Button(button_frame, text="🔧 Test Database", 
                                command=self.test_database)
        test_btn.pack(side=tk.LEFT, padx=5)
        
        # Exit button
        exit_btn = ttk.Button(button_frame, text="❌ Exit", 
                               command=self.root.quit)
        exit_btn.pack(side=tk.LEFT, padx=5)
    
    def load_known_faces(self):
        """Load known face encodings from database"""
        try:
            students = self.db.get_all_students()
            known_face_encodings = []
            known_face_names = []
            
            for student in students:
                if student.get('face_encoding'):
                    encoding = np.fromstring(student['face_encoding'], sep=',')
                    known_face_encodings.append(encoding)
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
    
    def test_database(self):
        """Test database connection and operations"""
        try:
            if self.db:
                # Test basic operations
                students = self.db.get_all_students()
                today = date.today().isoformat()
                attendance = self.db.get_attendance_with_emotions(today)
                
                message = f"✅ Database Test Successful!\n\n"
                message += f"📊 Total Students: {len(students)}\n"
                message += f"📈 Today's Attendance: {len(attendance)}\n"
                message += f"🗄️ Database: attendance_system\n"
                message += f"🔗 Host: localhost\n"
                message += f"👤 User: root"
                
                messagebox.showinfo("Database Test", message)
            else:
                messagebox.showerror("Error", "No database connection available")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Database test failed: {e}")
    
    def register_student_with_camera(self):
        """Register student using camera capture"""
        try:
            # Ask for student name
            name = tk.simpledialog.askstring("Register Student with Camera", "Enter student name:")
            if not name:
                return
            
            # Initialize camera
            print("📹 Initializing camera for registration...")
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                messagebox.showerror("Camera Error", "Could not open camera")
                return
            
            print("✅ Camera opened successfully!")
            print("📸 Position student in front of camera...")
            print("⌨️ Press 'c' to capture, 'q' to cancel")
            
            # Camera capture loop
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Show frame
                cv2.imshow('Student Registration', frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('c'):
                    print("📸 Capturing image...")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{name}_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"✅ Image saved as {filename}")
                    
                    # Add to database
                    if FACE_RECOGNITION_AVAILABLE:
                        image = face_recognition.load_image_file(filename)
                        face_encodings = face_recognition.face_encodings(image)
                        if face_encodings:
                            student_id = self.db.add_student(name, face_encodings[0], filename)
                            if student_id:
                                messagebox.showinfo("Success", f"Student {name} registered successfully with photo!")
                                self.load_known_faces()
                                break
                    else:
                        # Add without face encoding
                        student_id = self.db.add_student(name, None, filename)
                        if student_id:
                            messagebox.showinfo("Success", f"Student {name} registered successfully!")
                            self.load_known_faces()
                            break
                elif key == ord('q'):
                    print("❌ Registration cancelled")
                    break
            
            # Cleanup
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            messagebox.showerror("Registration Error", f"Camera registration failed: {e}")
    
    def register_student_basic(self):
        """Basic student registration without camera"""
        try:
            # Ask for student name
            name = tk.simpledialog.askstring("Register Student", "Enter student name:")
            if not name:
                return
            
            # Ask for image file
            image_path = filedialog.askopenfilename(
                title="Select student image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png")]
            )
            
            if not image_path:
                return
            
            # Load and process image
            if FACE_RECOGNITION_AVAILABLE:
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)
                
                if not face_encodings:
                    messagebox.showerror("Error", "No face found in image")
                    return
                
                # Add to database
                student_id = self.db.add_student(name, face_encodings[0], image_path)
                
                if student_id:
                    messagebox.showinfo("Success", f"Student {name} registered successfully!")
                    self.load_known_faces()
                else:
                    messagebox.showerror("Error", "Failed to register student")
            else:
                messagebox.showinfo("Info", "Face recognition not available. Please install face_recognition library.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")
    
    def show_attendance_basic(self):
        """Show attendance in a basic window"""
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
        print("🚀 Starting Basic MySQL GUI...")
        app = BasicMySQLAttendanceGUI()
        if hasattr(app, 'root'):
            print("✅ GUI initialized successfully")
            app.run()
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
