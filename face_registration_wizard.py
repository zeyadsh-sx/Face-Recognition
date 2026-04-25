#!/usr/bin/env python3
"""
Face Registration Wizard GUI - Advanced Step-by-Step Registration
Provides a professional wizard interface for registering student faces
"""

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import threading
from database_core_mysql import MySQLAttendanceDatabase


class FaceRegistrationWizard:
    """Professional wizard for face registration with step-by-step guidance"""
    
    def __init__(self, db=None):
        self.db = db
        
        # Wizard state
        self.current_step = 1
        self.total_steps = 5
        self.wizard_data = {
            'name': '',
            'student_id': '',
            'email': '',
            'phone': '',
            'images': [],
            'face_encodings': []
        }
        
        # GUI elements
        self.wizard_window = None
        self.main_frame = None
        self.step_labels = {}
        self.preview_label = None
        self.camera_running = False
        self.camera_thread = None
        
        # Setup
        self.setup_wizard_ui()
    
    def setup_wizard_ui(self):
        """Create the wizard window and layout"""
        self.wizard_window = tk.Tk()
        self.wizard_window.title("👤 Face Registration Wizard")
        self.wizard_window.geometry("900x700")
        self.wizard_window.configure(bg='#f5f5f5')
        
        # Prevent closing without confirmation
        self.wizard_window.protocol("WM_DELETE_WINDOW", self.on_close_wizard)
        
        # Create main container
        container = ttk.Frame(self.wizard_window)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Progress bar at top
        self.setup_progress_bar(container)
        
        # Main frame (will hold different step frames)
        self.main_frame = ttk.Frame(container)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Show first step
        self.show_step(1)
        
        # Bottom button frame
        self.setup_button_frame(container)
    
    def setup_progress_bar(self, parent):
        """Setup progress indicator at the top"""
        progress_frame = ttk.Frame(parent, relief=tk.SUNKEN, height=80, padding=15)
        progress_frame.grid(row=0, column=0, sticky="ew")
        
        # Title
        title_label = ttk.Label(progress_frame, text="👤 Face Registration Wizard", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Step indicators
        step_container = ttk.Frame(progress_frame)
        step_container.pack(fill=tk.X)
        
        steps = [
            ("1", "📋 Personal Info"),
            ("2", "📸 Capture Images"),
            ("3", "🔍 Review Images"),
            ("4", "✓ Verify Face"),
            ("5", "✅ Complete")
        ]
        
        for i, (num, label) in enumerate(steps):
            # Step circle
            step_frame = ttk.Frame(step_container)
            step_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            # Circle and label
            circle_label = ttk.Label(step_frame, text=num, font=('Arial', 11, 'bold'),
                                    relief=tk.SUNKEN, width=3, anchor=tk.CENTER)
            circle_label.pack(side=tk.LEFT, padx=5)
            self.step_labels[i+1] = circle_label
            
            text_label = ttk.Label(step_frame, text=label, font=('Arial', 9))
            text_label.pack(side=tk.LEFT, padx=5)
            
            # Arrow
            if i < len(steps) - 1:
                arrow = ttk.Label(step_container, text="→", font=('Arial', 12))
                arrow.pack(side=tk.LEFT)
        
        # Update colors
        self.update_step_indicators()
    
    def setup_button_frame(self, parent):
        """Setup navigation buttons at bottom"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=15)
        
        # Back button
        self.back_btn = ttk.Button(button_frame, text="◀ Back", 
                                   command=self.go_back_step, state=tk.DISABLED)
        self.back_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="✗ Cancel", 
                               command=self.on_close_wizard)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress text
        self.progress_label = ttk.Label(button_frame, text="", font=('Arial', 9))
        self.progress_label.pack(side=tk.LEFT, padx=20)
        
        # Next/Complete button
        self.next_btn = ttk.Button(button_frame, text="Next ▶", 
                                  command=self.go_next_step)
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        self.update_button_states()
    
    def update_step_indicators(self):
        """Update visual indicators for current step"""
        for step_num, label_widget in self.step_labels.items():
            if step_num < self.current_step:
                label_widget.configure(relief=tk.RAISED, foreground='#00aa00')
            elif step_num == self.current_step:
                label_widget.configure(relief=tk.SUNKEN, foreground='#0066cc')
            else:
                label_widget.configure(relief=tk.RAISED, foreground='#666666')
    
    def update_button_states(self):
        """Update button availability"""
        # Back button
        if self.current_step > 1:
            self.back_btn.config(state=tk.NORMAL)
        else:
            self.back_btn.config(state=tk.DISABLED)
        
        # Progress label
        self.progress_label.config(text=f"Step {self.current_step} of {self.total_steps}")
        
        # Next button
        if self.current_step == self.total_steps:
            self.next_btn.config(text="✓ Complete Registration")
        else:
            self.next_btn.config(text="Next ▶")
    
    def show_step(self, step_num):
        """Display the specified step"""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.current_step = step_num
        self.update_step_indicators()
        self.update_button_states()
        
        if step_num == 1:
            self.step_personal_info()
        elif step_num == 2:
            self.step_capture_images()
        elif step_num == 3:
            self.step_review_images()
        elif step_num == 4:
            self.step_verify_face()
        elif step_num == 5:
            self.step_complete()
    
    def step_personal_info(self):
        """Step 1: Collect personal information"""
        frame = ttk.LabelFrame(self.main_frame, text="📋 Student Information", padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Full Name
        ttk.Label(frame, text="Full Name:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=10)
        name_entry = ttk.Entry(frame, width=40, font=('Arial', 11))
        name_entry.grid(row=0, column=1, sticky=tk.EW, pady=10, padx=10)
        name_entry.insert(0, self.wizard_data['name'])
        name_entry.bind('<KeyRelease>', lambda e: self.update_wizard_data('name', name_entry.get()))
        
        # Student ID
        ttk.Label(frame, text="Student ID:", font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=10)
        sid_entry = ttk.Entry(frame, width=40, font=('Arial', 11))
        sid_entry.grid(row=1, column=1, sticky=tk.EW, pady=10, padx=10)
        sid_entry.insert(0, self.wizard_data['student_id'])
        sid_entry.bind('<KeyRelease>', lambda e: self.update_wizard_data('student_id', sid_entry.get()))
        
        # Email
        ttk.Label(frame, text="Email (Optional):", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=10)
        email_entry = ttk.Entry(frame, width=40, font=('Arial', 11))
        email_entry.grid(row=2, column=1, sticky=tk.EW, pady=10, padx=10)
        email_entry.insert(0, self.wizard_data['email'])
        email_entry.bind('<KeyRelease>', lambda e: self.update_wizard_data('email', email_entry.get()))
        
        # Phone
        ttk.Label(frame, text="Phone (Optional):", font=('Arial', 11, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=10)
        phone_entry = ttk.Entry(frame, width=40, font=('Arial', 11))
        phone_entry.grid(row=3, column=1, sticky=tk.EW, pady=10, padx=10)
        phone_entry.insert(0, self.wizard_data['phone'])
        phone_entry.bind('<KeyRelease>', lambda e: self.update_wizard_data('phone', phone_entry.get()))
        
        # Configure grid
        frame.grid_columnconfigure(1, weight=1)
        
        # Info message
        info_frame = ttk.LabelFrame(self.main_frame, text="ℹ️ Information", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        info_label = ttk.Label(info_frame, text="• At least Full Name and Student ID are required\n• This information will be saved to the database",
                              font=('Arial', 9), justify=tk.LEFT)
        info_label.pack()
    
    def step_capture_images(self):
        """Step 2: Capture face images"""
        frame = ttk.LabelFrame(self.main_frame, text="📸 Capture Face Images", padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instruction_text = ttk.Label(frame, 
            text="Choose how to capture face images:\n• Camera: Capture real-time from webcam\n• File: Select image(s) from your computer\n• Multiple images recommended for better accuracy",
            font=('Arial', 10), justify=tk.LEFT, foreground='#333333')
        instruction_text.pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        camera_btn = ttk.Button(button_frame, text="📹 Capture from Camera", 
                               command=self.capture_from_camera)
        camera_btn.pack(side=tk.LEFT, padx=10)
        
        file_btn = ttk.Button(button_frame, text="📁 Select from File", 
                             command=self.capture_from_file)
        file_btn.pack(side=tk.LEFT, padx=10)
        
        # Display captured images count
        images_label = ttk.Label(frame, text=f"Images captured: {len(self.wizard_data['images'])}/3",
                               font=('Arial', 11, 'bold'), foreground='#0066cc')
        images_label.pack(pady=10)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        if self.wizard_data['images']:
            # Show thumbnails
            for i, img_path in enumerate(self.wizard_data['images'][:3]):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((120, 120))
                    photo = ImageTk.PhotoImage(img)
                    
                    thumb_frame = ttk.Frame(preview_frame)
                    thumb_frame.pack(side=tk.LEFT, padx=5)
                    
                    img_label = ttk.Label(thumb_frame, image=photo)
                    img_label.image = photo
                    img_label.pack()
                    
                    remove_btn = ttk.Button(thumb_frame, text="Remove", 
                                          command=lambda x=i: self.remove_image(x))
                    remove_btn.pack()
                except:
                    pass
        else:
            ttk.Label(preview_frame, text="No images captured yet", 
                     font=('Arial', 10), foreground='#999999').pack(pady=30)
    
    def step_review_images(self):
        """Step 3: Review captured images"""
        frame = ttk.LabelFrame(self.main_frame, text="🔍 Review Images", padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        if not self.wizard_data['images']:
            ttk.Label(frame, text="No images captured yet. Please go back to capture images.",
                     font=('Arial', 11), foreground='#cc0000').pack(pady=30)
            return
        
        # Image display
        try:
            img = Image.open(self.wizard_data['images'][0])
            img.thumbnail((500, 500))
            photo = ImageTk.PhotoImage(img)
            
            img_label = ttk.Label(frame, image=photo)
            img_label.image = photo
            img_label.pack(pady=10)
            
            # Image info
            info_text = f"Image 1 of {len(self.wizard_data['images'])}\n"
            info_text += f"File: {os.path.basename(self.wizard_data['images'][0])}"
            ttk.Label(frame, text=info_text, font=('Arial', 9), 
                     foreground='#666666').pack(pady=5)
            
            # Navigation
            nav_frame = ttk.Frame(frame)
            nav_frame.pack(pady=10)
            
            prev_btn = ttk.Button(nav_frame, text="◀ Previous")
            prev_btn.pack(side=tk.LEFT, padx=5)
            
            next_btn = ttk.Button(nav_frame, text="Next ▶")
            next_btn.pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            ttk.Label(frame, text=f"Error loading image: {e}",
                     font=('Arial', 11), foreground='#cc0000').pack(pady=30)
    
    def step_verify_face(self):
        """Step 4: Verify and process faces"""
        frame = ttk.LabelFrame(self.main_frame, text="✓ Verify Face Recognition", padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        if not FACE_RECOGNITION_AVAILABLE:
            ttk.Label(frame, text="⚠️ Face recognition library not available\nPlease install: pip install face-recognition",
                     font=('Arial', 11), foreground='#cc6600').pack(pady=20)
            return
        
        # Process images and extract encodings
        status_text = ttk.Label(frame, text="Processing face encodings...",
                              font=('Arial', 11), foreground='#0066cc')
        status_text.pack(pady=20)
        self.wizard_window.update()
        
        try:
            encodings_found = 0
            for img_path in self.wizard_data['images']:
                try:
                    image = face_recognition.load_image_file(img_path)
                    face_encodings = face_recognition.face_encodings(image)
                    if face_encodings:
                        # Use the first face found
                        self.wizard_data['face_encodings'].append(face_encodings[0])
                        encodings_found += 1
                except:
                    pass
            
            if encodings_found > 0:
                status_text.config(text=f"✅ Successfully processed {encodings_found} face(s)!",
                                 foreground='#00aa00')
                
                # Show details
                details = ttk.Label(frame, 
                    text=f"• Face encodings extracted: {encodings_found}\n• Student name: {self.wizard_data['name']}\n• Average will be used for recognition",
                    font=('Arial', 10), justify=tk.LEFT)
                details.pack(pady=20, anchor=tk.W)
            else:
                status_text.config(text="❌ No faces found in images!",
                                 foreground='#cc0000')
                ttk.Label(frame, text="Please go back and capture clearer images of the face.",
                         font=('Arial', 10), foreground='#666666').pack(pady=10)
                
        except Exception as e:
            status_text.config(text=f"Error: {e}", foreground='#cc0000')
    
    def step_complete(self):
        """Step 5: Complete registration"""
        frame = ttk.LabelFrame(self.main_frame, text="✅ Complete Registration", padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary
        summary_frame = ttk.LabelFrame(frame, text="📝 Registration Summary", padding=15)
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        summary_text = f"""
Name:           {self.wizard_data['name']}
Student ID:     {self.wizard_data['student_id']}
Email:          {self.wizard_data['email'] or 'N/A'}
Phone:          {self.wizard_data['phone'] or 'N/A'}

Images:         {len(self.wizard_data['images'])}
Face Encodings: {len(self.wizard_data['face_encodings'])}
Status:         Ready to register ✅
"""
        
        summary_label = ttk.Label(summary_frame, text=summary_text, 
                                 font=('Courier', 10), justify=tk.LEFT)
        summary_label.pack(anchor=tk.W, pady=10)
        
        # Confirmation
        confirm_frame = ttk.LabelFrame(frame, text="Confirm", padding=15)
        confirm_frame.pack(fill=tk.X, pady=10)
        
        confirm_label = ttk.Label(confirm_frame, 
            text="Click 'Complete Registration' to save this student to the database.",
            font=('Arial', 10), foreground='#0066cc')
        confirm_label.pack()
        
        # Update next button
        self.next_btn.config(text="✓ Complete Registration")
    
    def update_wizard_data(self, field, value):
        """Update wizard data dictionary"""
        self.wizard_data[field] = value
    
    def capture_from_camera(self):
        """Capture image from camera"""
        if len(self.wizard_data['images']) >= 3:
            messagebox.showwarning("Limit Reached", "Maximum 3 images allowed")
            return
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open camera")
            return
        
        captured = False
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Display frame
                cv2.imshow('Press C to Capture, Q to Cancel', frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('c'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"temp_face_{len(self.wizard_data['images'])}_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    self.wizard_data['images'].append(filename)
                    captured = True
                    break
                elif key == ord('q') or key == 27:
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        if captured:
            messagebox.showinfo("Success", "Image captured successfully!")
            self.show_step(2)
    
    def capture_from_file(self):
        """Select images from file"""
        if len(self.wizard_data['images']) >= 3:
            messagebox.showwarning("Limit Reached", "Maximum 3 images allowed")
            return
        
        files = filedialog.askopenfilenames(
            title="Select face image(s)",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if files:
            for file in files:
                if len(self.wizard_data['images']) < 3:
                    self.wizard_data['images'].append(file)
            self.show_step(2)
    
    def remove_image(self, index):
        """Remove image at index"""
        if 0 <= index < len(self.wizard_data['images']):
            del self.wizard_data['images'][index]
            self.show_step(2)
    
    def go_next_step(self):
        """Move to next step"""
        if self.current_step == 1:
            # Validate step 1
            if not self.wizard_data['name'] or not self.wizard_data['student_id']:
                messagebox.showwarning("Missing Info", "Please enter name and student ID")
                return
            self.show_step(2)
        elif self.current_step == 2:
            # Validate step 2
            if not self.wizard_data['images']:
                messagebox.showwarning("Missing Images", "Please capture at least one image")
                return
            self.show_step(3)
        elif self.current_step == 3:
            self.show_step(4)
        elif self.current_step == 4:
            # Validate step 4
            if not self.wizard_data['face_encodings']:
                messagebox.showwarning("No Faces Found", "Please go back and capture clearer face images")
                return
            self.show_step(5)
        elif self.current_step == 5:
            # Complete registration
            self.complete_registration()
    
    def go_back_step(self):
        """Move to previous step"""
        if self.current_step > 1:
            self.show_step(self.current_step - 1)
    
    def complete_registration(self):
        """Save registration to database"""
        try:
            if not self.db:
                messagebox.showerror("Error", "Database not available")
                return
            
            # Average the encodings if multiple
            if self.wizard_data['face_encodings']:
                avg_encoding = np.mean(self.wizard_data['face_encodings'], axis=0)
            else:
                messagebox.showerror("Error", "No face encodings found")
                return
            
            # Save to database
            student_id = self.db.add_student(
                name=self.wizard_data['name'],
                face_encoding=avg_encoding,
                image_path=self.wizard_data['images'][0] if self.wizard_data['images'] else None,
                student_id=self.wizard_data['student_id'],
                email=self.wizard_data['email'],
                phone=self.wizard_data['phone']
            )
            
            if student_id:
                messagebox.showinfo("Success", 
                    f"✅ Student '{self.wizard_data['name']}' registered successfully!\n\n"
                    f"Student ID: {student_id}")
                self.wizard_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to register student")
                
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")
    
    def on_close_wizard(self):
        """Handle wizard closing"""
        if self.current_step > 1:
            if messagebox.askyesno("Cancel Registration", 
                                  "Are you sure? All progress will be lost."):
                self.wizard_window.destroy()
        else:
            self.wizard_window.destroy()
    
    def run(self):
        """Run the wizard"""
        self.wizard_window.mainloop()


if __name__ == "__main__":
    # Test standalone
    try:
        print("🚀 Starting Face Registration Wizard...")
        wizard = FaceRegistrationWizard()
        wizard.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
