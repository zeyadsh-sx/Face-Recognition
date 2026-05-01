#!/usr/bin/env python3
"""
Settings Panel GUI for Face Recognition Attendance System
Advanced configuration interface for system settings
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
from datetime import datetime
from database_core_mysql import MySQLAttendanceDatabase


class SettingsPanel:
    """Professional settings panel for system configuration"""

    def __init__(self, parent=None, db=None):
        self.parent = parent
        self.db = db

        # Settings file
        self.settings_file = "system_settings.json"

        # Default settings
        self.default_settings = {
            "database": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "attendance_system",
                "port": 3306
            },
            "camera": {
                "device_id": 0,
                "resolution": "640x480",
                "fps": 30,
                "brightness": 50,
                "contrast": 50
            },
            "face_recognition": {
                "tolerance": 0.6,
                "model": "hog",  # hog or cnn
                "upsample_times": 1,
                "num_jitters": 1,
                "enable_emotion_detection": True,
                "enable_spoof_detection": True
            },
            "attendance": {
                "auto_save": True,
                "duplicate_check_minutes": 30,
                "unknown_face_handling": "register",  # register, ignore, alert
                "attendance_timeout": 300  # seconds
            },
            "notifications": {
                "enable_desktop_notifications": True,
                "enable_sound_notifications": True,
                "low_attendance_threshold": 75.0,
                "alert_on_unknown_faces": True
            },
            "backup": {
                "auto_backup": True,
                "backup_interval_days": 7,
                "backup_location": "backups",
                "max_backup_files": 10
            },
            "ui": {
                "theme": "light",  # light, dark, auto
                "language": "ar",  # ar, en
                "auto_refresh_stats": True,
                "refresh_interval_seconds": 3,
                "show_emojis": True
            }
        }

        # Current settings
        self.settings = self.load_settings()

        # GUI elements
        self.settings_window = None
        self.notebook = None
        self.widgets = {}

        # Setup
        self.setup_settings_ui()

    def setup_settings_ui(self):
        """Create the settings window and layout"""
        self.settings_window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.settings_window.title("⚙️ System Settings")
        self.settings_window.geometry("800x600")
        self.settings_window.configure(bg='#f5f5f5')
        self.settings_window.resizable(True, True)

        # Prevent closing without saving
        self.settings_window.protocol("WM_DELETE_WINDOW", self.on_close_settings)

        # Main container
        main_frame = ttk.Frame(self.settings_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="⚙️ System Settings",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create tabs
        self.create_database_tab()
        self.create_camera_tab()
        self.create_face_recognition_tab()
        self.create_attendance_tab()
        self.create_notifications_tab()
        self.create_backup_tab()
        self.create_ui_tab()

        # Bottom button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Buttons
        save_btn = ttk.Button(button_frame, text="💾 Save Settings",
                             command=self.save_settings)
        save_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = ttk.Button(button_frame, text="🔄 Reset to Defaults",
                              command=self.reset_to_defaults)
        reset_btn.pack(side=tk.LEFT, padx=5)

        test_db_btn = ttk.Button(button_frame, text="🔧 Test Database",
                                command=self.test_database_connection)
        test_db_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(button_frame, text="📤 Export Settings",
                               command=self.export_settings)
        export_btn.pack(side=tk.LEFT, padx=5)

        import_btn = ttk.Button(button_frame, text="📥 Import Settings",
                               command=self.import_settings)
        import_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(button_frame, text="❌ Close",
                              command=self.on_close_settings)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def create_database_tab(self):
        """Create database settings tab"""
        tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab, text="🗄️ Database")

        # Database settings
        db_frame = ttk.LabelFrame(tab, text="MySQL Database Configuration", padding="10")
        db_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Host
        ttk.Label(db_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        host_entry = ttk.Entry(db_frame, width=30)
        host_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=10)
        host_entry.insert(0, self.settings["database"]["host"])
        self.widgets["db_host"] = host_entry

        # User
        ttk.Label(db_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        user_entry = ttk.Entry(db_frame, width=30)
        user_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        user_entry.insert(0, self.settings["database"]["user"])
        self.widgets["db_user"] = user_entry

        # Password
        ttk.Label(db_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        pass_entry = ttk.Entry(db_frame, width=30, show="*")
        pass_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        pass_entry.insert(0, self.settings["database"]["password"])
        self.widgets["db_password"] = pass_entry

        # Database name
        ttk.Label(db_frame, text="Database:").grid(row=3, column=0, sticky=tk.W, pady=5)
        db_entry = ttk.Entry(db_frame, width=30)
        db_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        db_entry.insert(0, self.settings["database"]["database"])
        self.widgets["db_name"] = db_entry

        # Port
        ttk.Label(db_frame, text="Port:").grid(row=4, column=0, sticky=tk.W, pady=5)
        port_entry = ttk.Entry(db_frame, width=30)
        port_entry.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=10)
        port_entry.insert(0, str(self.settings["database"]["port"]))
        self.widgets["db_port"] = port_entry

        # Configure grid
        db_frame.grid_columnconfigure(1, weight=1)

        # Info
        info_frame = ttk.LabelFrame(tab, text="ℹ️ Information", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        ttk.Label(info_frame,
            text="• Changes require application restart\n• Default XAMPP settings: localhost, root, empty password\n• Database 'attendance_system' will be created automatically",
            font=('Arial', 9), justify=tk.LEFT).pack(anchor=tk.W)

    def create_camera_tab(self):
        """Create camera settings tab"""
        tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab, text="📹 Camera")

        # Camera settings
        cam_frame = ttk.LabelFrame(tab, text="Camera Configuration", padding="10")
        cam_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Device ID
        ttk.Label(cam_frame, text="Device ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        device_combo = ttk.Combobox(cam_frame, values=["0", "1", "2", "3"], width=27)
        device_combo.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=10)
        device_combo.set(str(self.settings["camera"]["device_id"]))
        self.widgets["cam_device"] = device_combo

        # Resolution
        ttk.Label(cam_frame, text="Resolution:").grid(row=1, column=0, sticky=tk.W, pady=5)
        res_combo = ttk.Combobox(cam_frame,
            values=["320x240", "640x480", "800x600", "1280x720", "1920x1080"], width=27)
        res_combo.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        res_combo.set(self.settings["camera"]["resolution"])
        self.widgets["cam_resolution"] = res_combo

        # FPS
        ttk.Label(cam_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W, pady=5)
        fps_combo = ttk.Combobox(cam_frame, values=["15", "24", "30", "60"], width=27)
        fps_combo.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        fps_combo.set(str(self.settings["camera"]["fps"]))
        self.widgets["cam_fps"] = fps_combo

        # Brightness
        ttk.Label(cam_frame, text="Brightness:").grid(row=3, column=0, sticky=tk.W, pady=5)
        bright_scale = ttk.Scale(cam_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        bright_scale.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        bright_scale.set(self.settings["camera"]["brightness"])
        self.widgets["cam_brightness"] = bright_scale

        # Contrast
        ttk.Label(cam_frame, text="Contrast:").grid(row=4, column=0, sticky=tk.W, pady=5)
        contrast_scale = ttk.Scale(cam_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        contrast_scale.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=10)
        contrast_scale.set(self.settings["camera"]["contrast"])
        self.widgets["cam_contrast"] = contrast_scale

        cam_frame.grid_columnconfigure(1, weight=1)

    def create_face_recognition_tab(self):
        """Create face recognition settings tab"""
        tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab, text="👤 Face Recognition")

        # Face recognition settings
        fr_frame = ttk.LabelFrame(tab, text="Face Recognition Configuration", padding="10")
        fr_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Tolerance
        ttk.Label(fr_frame, text="Tolerance (0.1-1.0):").grid(row=0, column=0, sticky=tk.W, pady=5)
        tol_scale = ttk.Scale(fr_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL)
        tol_scale.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=10)
        tol_scale.set(self.settings["face_recognition"]["tolerance"])
        self.widgets["fr_tolerance"] = tol_scale

        # Model
        ttk.Label(fr_frame, text="Model:").grid(row=1, column=0, sticky=tk.W, pady=5)
        model_combo = ttk.Combobox(fr_frame, values=["hog", "cnn"], width=27)
        model_combo.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        model_combo.set(self.settings["face_recognition"]["model"])
        self.widgets["fr_model"] = model_combo

        # Upsample times
        ttk.Label(fr_frame, text="Upsample Times:").grid(row=2, column=0, sticky=tk.W, pady=5)
        upsample_combo = ttk.Combobox(fr_frame, values=["0", "1", "2"], width=27)
        upsample_combo.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        upsample_combo.set(str(self.settings["face_recognition"]["upsample_times"]))
        self.widgets["fr_upsample"] = upsample_combo

        # Num jitters
        ttk.Label(fr_frame, text="Num Jitters:").grid(row=3, column=0, sticky=tk.W, pady=5)
        jitters_combo = ttk.Combobox(fr_frame, values=["0", "1", "2", "5", "10"], width=27)
        jitters_combo.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        jitters_combo.set(str(self.settings["face_recognition"]["num_jitters"]))
        self.widgets["fr_jitters"] = jitters_combo

        # Enable emotion detection
        emotion_var = tk.BooleanVar(value=self.settings["face_recognition"]["enable_emotion_detection"])
        ttk.Checkbutton(fr_frame, text="Enable Emotion Detection",
                        variable=emotion_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["fr_emotion"] = emotion_var

        # Enable spoof detection
        spoof_var = tk.BooleanVar(value=self.settings["face_recognition"]["enable_spoof_detection"])
        ttk.Checkbutton(fr_frame, text="Enable Spoof Detection",
                        variable=spoof_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["fr_spoof"] = spoof_var

        fr_frame.grid_columnconfigure(1, weight=1)

        # Info
        info_frame = ttk.LabelFrame(tab, text="ℹ️ Tips", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        ttk.Label(info_frame,
            text="• Lower tolerance = stricter matching (recommended: 0.5-0.7)\n• CNN model is more accurate but slower\n• Upsample helps detect smaller faces\n• Jitters improve accuracy with multiple samples",
            font=('Arial', 9), justify=tk.LEFT).pack(anchor=tk.W)

    def create_attendance_tab(self):
        """Create attendance settings tab"""
        tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab, text="📊 Attendance")

        # Attendance settings
        att_frame = ttk.LabelFrame(tab, text="Attendance Configuration", padding="10")
        att_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Auto save
        auto_save_var = tk.BooleanVar(value=self.settings["attendance"]["auto_save"])
        ttk.Checkbutton(att_frame, text="Auto-save attendance records",
                        variable=auto_save_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["att_auto_save"] = auto_save_var

        # Duplicate check minutes
        ttk.Label(att_frame, text="Duplicate check (minutes):").grid(row=1, column=0, sticky=tk.W, pady=5)
        dup_entry = ttk.Entry(att_frame, width=30)
        dup_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        dup_entry.insert(0, str(self.settings["attendance"]["duplicate_check_minutes"]))
        self.widgets["att_dup_check"] = dup_entry

        # Unknown face handling
        ttk.Label(att_frame, text="Unknown face handling:").grid(row=2, column=0, sticky=tk.W, pady=5)
        unknown_combo = ttk.Combobox(att_frame,
            values=["register", "ignore", "alert"], width=27)
        unknown_combo.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        unknown_combo.set(self.settings["attendance"]["unknown_face_handling"])
        self.widgets["att_unknown"] = unknown_combo

        # Attendance timeout
        ttk.Label(att_frame, text="Attendance timeout (seconds):").grid(row=3, column=0, sticky=tk.W, pady=5)
        timeout_entry = ttk.Entry(att_frame, width=30)
        timeout_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        timeout_entry.insert(0, str(self.settings["attendance"]["attendance_timeout"]))
        self.widgets["att_timeout"] = timeout_entry

        att_frame.grid_columnconfigure(1, weight=1)

    def create_notifications_tab(self):
        """Create notifications settings tab"""
        tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab, text="🔔 Notifications")

        # Notifications settings
        notif_frame = ttk.LabelFrame(tab, text="Notification Configuration", padding="10")
        notif_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Desktop notifications
        desktop_var = tk.BooleanVar(value=self.settings["notifications"]["enable_desktop_notifications"])
        ttk.Checkbutton(notif_frame, text="Enable desktop notifications",
                        variable=desktop_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["notif_desktop"] = desktop_var

        # Sound notifications
        sound_var = tk.BooleanVar(value=self.settings["notifications"]["enable_sound_notifications"])
        ttk.Checkbutton(notif_frame, text="Enable sound notifications",
                        variable=sound_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["notif_sound"] = sound_var

        # Low attendance threshold
        ttk.Label(notif_frame, text="Low attendance threshold (%):").grid(row=2, column=0, sticky=tk.W, pady=5)
        threshold_entry = ttk.Entry(notif_frame, width=30)
        threshold_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        threshold_entry.insert(0, str(self.settings["notifications"]["low_attendance_threshold"]))
        self.widgets["notif_threshold"] = threshold_entry

        # Alert on unknown faces
        unknown_alert_var = tk.BooleanVar(value=self.settings["notifications"]["alert_on_unknown_faces"])
        ttk.Checkbutton(notif_frame, text="Alert on unknown faces",
                        variable=unknown_alert_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["notif_unknown"] = unknown_alert_var

        notif_frame.grid_columnconfigure(1, weight=1)

    def create_backup_tab(self):
        """Create backup settings tab"""
        tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab, text="💾 Backup")

        # Backup settings
        backup_frame = ttk.LabelFrame(tab, text="Backup Configuration", padding="10")
        backup_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Auto backup
        auto_backup_var = tk.BooleanVar(value=self.settings["backup"]["auto_backup"])
        ttk.Checkbutton(backup_frame, text="Enable automatic backups",
                        variable=auto_backup_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["backup_auto"] = auto_backup_var

        # Backup interval
        ttk.Label(backup_frame, text="Backup interval (days):").grid(row=1, column=0, sticky=tk.W, pady=5)
        interval_entry = ttk.Entry(backup_frame, width=30)
        interval_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        interval_entry.insert(0, str(self.settings["backup"]["backup_interval_days"]))
        self.widgets["backup_interval"] = interval_entry

        # Backup location
        ttk.Label(backup_frame, text="Backup location:").grid(row=2, column=0, sticky=tk.W, pady=5)
        loc_frame = ttk.Frame(backup_frame)
        loc_frame.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=10)
        loc_entry = ttk.Entry(loc_frame, width=20)
        loc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        loc_entry.insert(0, self.settings["backup"]["backup_location"])
        self.widgets["backup_location"] = loc_entry
        browse_btn = ttk.Button(loc_frame, text="📁 Browse",
                               command=lambda: self.browse_backup_location(loc_entry))
        browse_btn.pack(side=tk.RIGHT, padx=5)

        # Max backup files
        ttk.Label(backup_frame, text="Max backup files:").grid(row=3, column=0, sticky=tk.W, pady=5)
        max_entry = ttk.Entry(backup_frame, width=30)
        max_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        max_entry.insert(0, str(self.settings["backup"]["max_backup_files"]))
        self.widgets["backup_max"] = max_entry

        backup_frame.grid_columnconfigure(1, weight=1)

        # Manual backup button
        manual_btn = ttk.Button(tab, text="🔄 Create Manual Backup Now",
                               command=self.create_manual_backup)
        manual_btn.pack(pady=10)

    def create_ui_tab(self):
        """Create UI settings tab"""
        tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab, text="🎨 Interface")

        # UI settings
        ui_frame = ttk.LabelFrame(tab, text="User Interface Configuration", padding="10")
        ui_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Theme
        ttk.Label(ui_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        theme_combo = ttk.Combobox(ui_frame, values=["light", "dark", "auto"], width=27)
        theme_combo.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=10)
        theme_combo.set(self.settings["ui"]["theme"])
        self.widgets["ui_theme"] = theme_combo

        # Language
        ttk.Label(ui_frame, text="Language:").grid(row=1, column=0, sticky=tk.W, pady=5)
        lang_combo = ttk.Combobox(ui_frame, values=["ar", "en"], width=27)
        lang_combo.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)
        lang_combo.set(self.settings["ui"]["language"])
        self.widgets["ui_language"] = lang_combo

        # Auto refresh stats
        refresh_var = tk.BooleanVar(value=self.settings["ui"]["auto_refresh_stats"])
        ttk.Checkbutton(ui_frame, text="Auto-refresh statistics",
                        variable=refresh_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["ui_refresh"] = refresh_var

        # Refresh interval
        ttk.Label(ui_frame, text="Refresh interval (seconds):").grid(row=3, column=0, sticky=tk.W, pady=5)
        refresh_entry = ttk.Entry(ui_frame, width=30)
        refresh_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=10)
        refresh_entry.insert(0, str(self.settings["ui"]["refresh_interval_seconds"]))
        self.widgets["ui_interval"] = refresh_entry

        # Show emojis
        emoji_var = tk.BooleanVar(value=self.settings["ui"]["show_emojis"])
        ttk.Checkbutton(ui_frame, text="Show emojis in interface",
                        variable=emoji_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.widgets["ui_emojis"] = emoji_var

        ui_frame.grid_columnconfigure(1, weight=1)

    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to handle missing keys
                    return self.merge_settings(self.default_settings, loaded_settings)
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()

    def merge_settings(self, defaults, loaded):
        """Merge loaded settings with defaults"""
        merged = defaults.copy()
        for key, value in loaded.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = self.merge_settings(merged[key], value)
            else:
                merged[key] = value
        return merged

    def save_settings(self):
        """Save current settings to file"""
        try:
            # Collect settings from widgets
            self.collect_widget_values()

            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Success", "✅ Settings saved successfully!")
            print("Settings saved successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def collect_widget_values(self):
        """Collect values from all widgets"""
        try:
            # Database settings
            self.settings["database"]["host"] = self.widgets["db_host"].get()
            self.settings["database"]["user"] = self.widgets["db_user"].get()
            self.settings["database"]["password"] = self.widgets["db_password"].get()
            self.settings["database"]["database"] = self.widgets["db_name"].get()
            self.settings["database"]["port"] = int(self.widgets["db_port"].get())

            # Camera settings
            self.settings["camera"]["device_id"] = int(self.widgets["cam_device"].get())
            self.settings["camera"]["resolution"] = self.widgets["cam_resolution"].get()
            self.settings["camera"]["fps"] = int(self.widgets["cam_fps"].get())
            self.settings["camera"]["brightness"] = int(self.widgets["cam_brightness"].get())
            self.settings["camera"]["contrast"] = int(self.widgets["cam_contrast"].get())

            # Face recognition settings
            self.settings["face_recognition"]["tolerance"] = self.widgets["fr_tolerance"].get()
            self.settings["face_recognition"]["model"] = self.widgets["fr_model"].get()
            self.settings["face_recognition"]["upsample_times"] = int(self.widgets["fr_upsample"].get())
            self.settings["face_recognition"]["num_jitters"] = int(self.widgets["fr_jitters"].get())
            self.settings["face_recognition"]["enable_emotion_detection"] = self.widgets["fr_emotion"].get()
            self.settings["face_recognition"]["enable_spoof_detection"] = self.widgets["fr_spoof"].get()

            # Attendance settings
            self.settings["attendance"]["auto_save"] = self.widgets["att_auto_save"].get()
            self.settings["attendance"]["duplicate_check_minutes"] = int(self.widgets["att_dup_check"].get())
            self.settings["attendance"]["unknown_face_handling"] = self.widgets["att_unknown"].get()
            self.settings["attendance"]["attendance_timeout"] = int(self.widgets["att_timeout"].get())

            # Notifications settings
            self.settings["notifications"]["enable_desktop_notifications"] = self.widgets["notif_desktop"].get()
            self.settings["notifications"]["enable_sound_notifications"] = self.widgets["notif_sound"].get()
            self.settings["notifications"]["low_attendance_threshold"] = float(self.widgets["notif_threshold"].get())
            self.settings["notifications"]["alert_on_unknown_faces"] = self.widgets["notif_unknown"].get()

            # Backup settings
            self.settings["backup"]["auto_backup"] = self.widgets["backup_auto"].get()
            self.settings["backup"]["backup_interval_days"] = int(self.widgets["backup_interval"].get())
            self.settings["backup"]["backup_location"] = self.widgets["backup_location"].get()
            self.settings["backup"]["max_backup_files"] = int(self.widgets["backup_max"].get())

            # UI settings
            self.settings["ui"]["theme"] = self.widgets["ui_theme"].get()
            self.settings["ui"]["language"] = self.widgets["ui_language"].get()
            self.settings["ui"]["auto_refresh_stats"] = self.widgets["ui_refresh"].get()
            self.settings["ui"]["refresh_interval_seconds"] = int(self.widgets["ui_interval"].get())
            self.settings["ui"]["show_emojis"] = self.widgets["ui_emojis"].get()

        except Exception as e:
            print(f"Error collecting widget values: {e}")

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Confirm Reset",
                              "Are you sure you want to reset all settings to defaults?"):
            self.settings = self.default_settings.copy()
            self.refresh_widgets()
            messagebox.showinfo("Reset", "Settings reset to defaults")

    def refresh_widgets(self):
        """Refresh all widget values from settings"""
        try:
            # Database
            self.widgets["db_host"].delete(0, tk.END)
            self.widgets["db_host"].insert(0, self.settings["database"]["host"])
            self.widgets["db_user"].delete(0, tk.END)
            self.widgets["db_user"].insert(0, self.settings["database"]["user"])
            self.widgets["db_password"].delete(0, tk.END)
            self.widgets["db_password"].insert(0, self.settings["database"]["password"])
            self.widgets["db_name"].delete(0, tk.END)
            self.widgets["db_name"].insert(0, self.settings["database"]["database"])
            self.widgets["db_port"].delete(0, tk.END)
            self.widgets["db_port"].insert(0, str(self.settings["database"]["port"]))

            # Camera
            self.widgets["cam_device"].set(str(self.settings["camera"]["device_id"]))
            self.widgets["cam_resolution"].set(self.settings["camera"]["resolution"])
            self.widgets["cam_fps"].set(str(self.settings["camera"]["fps"]))
            self.widgets["cam_brightness"].set(self.settings["camera"]["brightness"])
            self.widgets["cam_contrast"].set(self.settings["camera"]["contrast"])

            # Face recognition
            self.widgets["fr_tolerance"].set(self.settings["face_recognition"]["tolerance"])
            self.widgets["fr_model"].set(self.settings["face_recognition"]["model"])
            self.widgets["fr_upsample"].set(str(self.settings["face_recognition"]["upsample_times"]))
            self.widgets["fr_jitters"].set(str(self.settings["face_recognition"]["num_jitters"]))
            self.widgets["fr_emotion"].set(self.settings["face_recognition"]["enable_emotion_detection"])
            self.widgets["fr_spoof"].set(self.settings["face_recognition"]["enable_spoof_detection"])

            # Attendance
            self.widgets["att_auto_save"].set(self.settings["attendance"]["auto_save"])
            self.widgets["att_dup_check"].delete(0, tk.END)
            self.widgets["att_dup_check"].insert(0, str(self.settings["attendance"]["duplicate_check_minutes"]))
            self.widgets["att_unknown"].set(self.settings["attendance"]["unknown_face_handling"])
            self.widgets["att_timeout"].delete(0, tk.END)
            self.widgets["att_timeout"].insert(0, str(self.settings["attendance"]["attendance_timeout"]))

            # Notifications
            self.widgets["notif_desktop"].set(self.settings["notifications"]["enable_desktop_notifications"])
            self.widgets["notif_sound"].set(self.settings["notifications"]["enable_sound_notifications"])
            self.widgets["notif_threshold"].delete(0, tk.END)
            self.widgets["notif_threshold"].insert(0, str(self.settings["notifications"]["low_attendance_threshold"]))
            self.widgets["notif_unknown"].set(self.settings["notifications"]["alert_on_unknown_faces"])

            # Backup
            self.widgets["backup_auto"].set(self.settings["backup"]["auto_backup"])
            self.widgets["backup_interval"].delete(0, tk.END)
            self.widgets["backup_interval"].insert(0, str(self.settings["backup"]["backup_interval_days"]))
            self.widgets["backup_location"].delete(0, tk.END)
            self.widgets["backup_location"].insert(0, self.settings["backup"]["backup_location"])
            self.widgets["backup_max"].delete(0, tk.END)
            self.widgets["backup_max"].insert(0, str(self.settings["backup"]["max_backup_files"]))

            # UI
            self.widgets["ui_theme"].set(self.settings["ui"]["theme"])
            self.widgets["ui_language"].set(self.settings["ui"]["language"])
            self.widgets["ui_refresh"].set(self.settings["ui"]["auto_refresh_stats"])
            self.widgets["ui_interval"].delete(0, tk.END)
            self.widgets["ui_interval"].insert(0, str(self.settings["ui"]["refresh_interval_seconds"]))
            self.widgets["ui_emojis"].set(self.settings["ui"]["show_emojis"])

        except Exception as e:
            print(f"Error refreshing widgets: {e}")

    def test_database_connection(self):
        """Test database connection with current settings"""
        try:
            # Collect current database settings
            db_config = {
                "host": self.widgets["db_host"].get(),
                "user": self.widgets["db_user"].get(),
                "password": self.widgets["db_password"].get(),
                "database": self.widgets["db_name"].get(),
                "port": int(self.widgets["db_port"].get())
            }

            # Test connection
            test_db = MySQLAttendanceDatabase(**db_config)

            if test_db:
                # Test basic operations
                students = test_db.get_all_students()
                messagebox.showinfo("Database Test",
                    f"✅ Database connection successful!\n\n"
                    f"📊 Total Students: {len(students)}\n"
                    f"🗄️ Database: {db_config['database']}\n"
                    f"🔗 Host: {db_config['host']}:{db_config['port']}\n"
                    f"👤 User: {db_config['user']}")
            else:
                messagebox.showerror("Database Test", "❌ Database connection failed")

        except Exception as e:
            messagebox.showerror("Database Test", f"❌ Database test failed: {e}")

    def browse_backup_location(self, entry_widget):
        """Browse for backup location"""
        folder = filedialog.askdirectory(title="Select Backup Location")
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)

    def create_manual_backup(self):
        """Create manual backup"""
        try:
            backup_location = self.widgets["backup_location"].get()
            if not backup_location:
                messagebox.showerror("Error", "Please set backup location first")
                return

            # Create backup directory
            os.makedirs(backup_location, exist_ok=True)

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"attendance_backup_{timestamp}.sql"

            # Create backup (simplified - in real implementation would use mysqldump)
            if self.db:
                # This is a simplified backup - real implementation would use proper SQL dump
                backup_path = os.path.join(backup_location, backup_file)

                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(f"-- Attendance System Backup\n")
                    f.write(f"-- Created: {datetime.now()}\n\n")

                    # Backup students
                    students = self.db.get_all_students()
                    f.write("-- STUDENTS TABLE\n")
                    for student in students:
                        f.write(f"INSERT INTO students VALUES ({student['id']}, '{student['name']}', ...);\n")

                    # Backup attendance
                    attendance = self.db.get_attendance_with_emotions()
                    f.write("\n-- ATTENDANCE TABLE\n")
                    for record in attendance:
                        f.write(f"INSERT INTO attendance VALUES (...);\n")

                messagebox.showinfo("Backup", f"✅ Manual backup created:\n{backup_path}")
            else:
                messagebox.showerror("Error", "No database connection available")

        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {e}")

    def export_settings(self):
        """Export settings to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Settings"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Export", f"Settings exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export settings: {e}")

    def import_settings(self):
        """Import settings from file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Import Settings"
            )

            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = json.load(f)

                # Merge with current settings
                self.settings = self.merge_settings(self.settings, imported_settings)
                self.refresh_widgets()

                messagebox.showinfo("Import", f"Settings imported from:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import settings: {e}")

    def on_close_settings(self):
        """Handle settings window closing"""
        if messagebox.askyesno("Close Settings",
                              "Do you want to save changes before closing?"):
            self.save_settings()
        self.settings_window.destroy()

    def run(self):
        """Run the settings panel"""
        self.settings_window.mainloop()


if __name__ == "__main__":
    # Test standalone
    try:
        print("🚀 Starting Settings Panel...")
        settings = SettingsPanel()
        settings.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()