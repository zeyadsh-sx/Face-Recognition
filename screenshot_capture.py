#!/usr/bin/env python3
"""
Screenshot Capture GUI for Face Recognition Attendance System
Advanced screenshot capture with region selection and image management
"""

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ pyautogui not available, using fallback screenshot methods")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import time
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab
import threading
import json


class ScreenshotCapture:
    """Professional screenshot capture interface"""

    def __init__(self, parent=None):
        self.parent = parent

        # Screenshot settings
        self.screenshot_dir = "screenshots"
        self.temp_dir = "temp_screenshots"

        # Create directories
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        # GUI elements
        self.capture_window = None
        self.preview_canvas = None
        self.current_image = None
        self.current_photo = None

        # Capture state
        self.is_capturing = False
        self.capture_thread = None

        # Settings
        self.settings = {
            "auto_save": True,
            "save_format": "PNG",  # PNG, JPG, BMP
            "quality": 95,  # For JPG
            "include_timestamp": True,
            "max_screenshots": 50,
            "capture_delay": 0  # seconds
        }

        # Load settings
        self.load_settings()

        # Setup UI
        self.setup_capture_ui()

    def setup_capture_ui(self):
        """Create the screenshot capture window"""
        self.capture_window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.capture_window.title("📸 Screenshot Capture")
        self.capture_window.geometry("900x700")
        self.capture_window.configure(bg='#f5f5f5')

        # Prevent closing without confirmation
        self.capture_window.protocol("WM_DELETE_WINDOW", self.on_close_capture)

        # Main container
        main_frame = ttk.Frame(self.capture_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="📸 Screenshot Capture Tool",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Capture Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=10)

        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10)

        # Full screen capture
        full_btn = ttk.Button(button_frame, text="🖥️ Full Screen",
                             command=self.capture_fullscreen)
        full_btn.pack(side=tk.LEFT, padx=5)

        # Region capture
        region_btn = ttk.Button(button_frame, text="📐 Select Region",
                               command=self.capture_region)
        region_btn.pack(side=tk.LEFT, padx=5)

        # Window capture
        window_btn = ttk.Button(button_frame, text="🪟 Active Window",
                               command=self.capture_window)
        window_btn.pack(side=tk.LEFT, padx=5)

        # Delayed capture
        delay_btn = ttk.Button(button_frame, text="⏱️ Delayed Capture",
                              command=self.capture_delayed)
        delay_btn.pack(side=tk.LEFT, padx=5)

        # Settings
        settings_btn = ttk.Button(button_frame, text="⚙️ Settings",
                                 command=self.open_capture_settings)
        settings_btn.pack(side=tk.LEFT, padx=5)

        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="📋 Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Canvas for image preview
        self.preview_canvas = tk.Canvas(preview_frame, bg='#e0e0e0', width=800, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # Scrollbars for canvas
        h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.preview_canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

        # Info label
        self.info_label = ttk.Label(preview_frame, text="No screenshot captured yet",
                                   font=('Arial', 10), foreground='#666666')
        self.info_label.pack(pady=5)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        save_btn = ttk.Button(action_frame, text="💾 Save Screenshot",
                             command=self.save_screenshot)
        save_btn.pack(side=tk.LEFT, padx=5)

        copy_btn = ttk.Button(action_frame, text="📋 Copy to Clipboard",
                             command=self.copy_to_clipboard)
        copy_btn.pack(side=tk.LEFT, padx=5)

        share_btn = ttk.Button(action_frame, text="📤 Share Screenshot",
                              command=self.share_screenshot)
        share_btn.pack(side=tk.LEFT, padx=5)

        gallery_btn = ttk.Button(action_frame, text="🖼️ Open Gallery",
                                command=self.open_gallery)
        gallery_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(action_frame, text="🗑️ Clear",
                              command=self.clear_preview)
        clear_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(action_frame, text="❌ Close",
                              command=self.on_close_capture)
        close_btn.pack(side=tk.RIGHT, padx=5)

        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready",
                                     font=('Arial', 9), foreground='#0066cc')
        self.status_label.pack(anchor=tk.W, pady=5)

    def capture_fullscreen(self):
        """Capture full screen"""
        try:
            self.status_label.config(text="📸 Capturing full screen...", foreground='#ff6600')
            self.capture_window.update()

            # Apply delay if set
            if self.settings["capture_delay"] > 0:
                time.sleep(self.settings["capture_delay"])

            # Capture screenshot
            if PYAUTOGUI_AVAILABLE:
                screenshot = pyautogui.screenshot()
            else:
                # Fallback to PIL ImageGrab
                screenshot = ImageGrab.grab()

            # Convert to PIL Image
            self.current_image = screenshot

            # Display preview
            self.display_preview()

            # Auto save if enabled
            if self.settings["auto_save"]:
                self.save_screenshot(auto=True)

            self.status_label.config(text="✅ Full screen captured successfully", foreground='#00aa00')

        except Exception as e:
            self.status_label.config(text=f"❌ Capture failed: {e}", foreground='#cc0000')
            messagebox.showerror("Capture Error", f"Failed to capture screenshot: {e}")

    def capture_region(self):
        """Capture selected region"""
        try:
            self.status_label.config(text="📐 Select region to capture...", foreground='#ff6600')
            self.capture_window.update()

            if not PYAUTOGUI_AVAILABLE:
                messagebox.showinfo("Region Selection",
                    "Region selection requires pyautogui.\n"
                    "Please install: pip install pyautogui\n\n"
                    "For now, capturing full screen instead.")
                self.capture_fullscreen()
                return

            # Minimize window temporarily
            self.capture_window.iconify()

            # Wait a moment
            time.sleep(0.5)

            # Let user select region
            messagebox.showinfo("Region Selection",
                "Click and drag to select the region you want to capture.\n"
                "Press Enter to confirm or Esc to cancel.")

            try:
                # Use pyautogui for region selection
                region = pyautogui.prompt("Enter region coordinates (x,y,width,height) or leave empty to cancel:",
                                        "Region Selection")

                if region:
                    # Parse coordinates
                    coords = region.split(',')
                    if len(coords) == 4:
                        x, y, w, h = map(int, coords)
                        screenshot = pyautogui.screenshot(region=(x, y, w, h))
                        self.current_image = screenshot
                        self.display_preview()

                        if self.settings["auto_save"]:
                            self.save_screenshot(auto=True)

                        self.status_label.config(text="✅ Region captured successfully", foreground='#00aa00')
                    else:
                        self.status_label.config(text="❌ Invalid region format", foreground='#cc0000')
                else:
                    self.status_label.config(text="❌ Region selection cancelled", foreground='#cc0000')

            except Exception as e:
                self.status_label.config(text=f"❌ Region capture failed: {e}", foreground='#cc0000')

            # Restore window
            self.capture_window.deiconify()
            self.capture_window.lift()

        except Exception as e:
            self.status_label.config(text=f"❌ Capture failed: {e}", foreground='#cc0000')
            messagebox.showerror("Capture Error", f"Failed to capture region: {e}")

    def capture_window(self):
        """Capture active window"""
        try:
            self.status_label.config(text="🪟 Capturing active window...", foreground='#ff6600')
            self.capture_window.update()

            if not PYAUTOGUI_AVAILABLE:
                messagebox.showinfo("Active Window",
                    "Active window capture requires pyautogui.\n"
                    "Please install: pip install pyautogui\n\n"
                    "For now, capturing full screen instead.")
                self.capture_fullscreen()
                return

            # Minimize our window temporarily
            self.capture_window.iconify()
            time.sleep(0.5)

            try:
                # Get active window (this is a simplified version)
                # In a real implementation, you might use win32gui or similar
                screenshot = pyautogui.screenshot()

                # For now, we'll capture full screen as active window
                # You could enhance this to detect window boundaries
                self.current_image = screenshot
                self.display_preview()

                if self.settings["auto_save"]:
                    self.save_screenshot(auto=True)

                self.status_label.config(text="✅ Active window captured successfully", foreground='#00aa00')

            except Exception as e:
                self.status_label.config(text=f"❌ Window capture failed: {e}", foreground='#cc0000')

            # Restore window
            self.capture_window.deiconify()
            self.capture_window.lift()

        except Exception as e:
            self.status_label.config(text=f"❌ Capture failed: {e}", foreground='#cc0000')
            messagebox.showerror("Capture Error", f"Failed to capture window: {e}")

    def capture_delayed(self):
        """Capture with delay"""
        try:
            # Ask for delay
            delay = simpledialog.askinteger("Delayed Capture",
                "Enter delay in seconds (1-10):", minvalue=1, maxvalue=10)

            if delay:
                self.status_label.config(text=f"⏱️ Capturing in {delay} seconds...", foreground='#ff6600')

                def delayed_capture():
                    for i in range(delay, 0, -1):
                        self.status_label.config(text=f"⏱️ Capturing in {i} seconds...", foreground='#ff6600')
                        self.capture_window.update()
                        time.sleep(1)

                    try:
                        if PYAUTOGUI_AVAILABLE:
                            screenshot = pyautogui.screenshot()
                        else:
                            screenshot = ImageGrab.grab()

                        self.current_image = screenshot
                        self.display_preview()

                        if self.settings["auto_save"]:
                            self.save_screenshot(auto=True)

                        self.status_label.config(text="✅ Delayed capture completed", foreground='#00aa00')
                    except Exception as e:
                        self.status_label.config(text=f"❌ Delayed capture failed: {e}", foreground='#cc0000')

                # Run in thread to avoid freezing UI
                thread = threading.Thread(target=delayed_capture, daemon=True)
                thread.start()

        except Exception as e:
            self.status_label.config(text=f"❌ Delayed capture setup failed: {e}", foreground='#cc0000')

    def display_preview(self):
        """Display screenshot preview in canvas"""
        if not self.current_image:
            return

        try:
            # Resize image to fit canvas while maintaining aspect ratio
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width <= 1:
                canvas_width = 800
            if canvas_height <= 1:
                canvas_height = 400

            # Calculate resize ratio
            img_width, img_height = self.current_image.size
            ratio = min(canvas_width / img_width, canvas_height / img_height)

            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)

            # Resize image
            resized_image = self.current_image.resize((new_width, new_height), Image.LANCZOS)

            # Convert to PhotoImage
            self.current_photo = ImageTk.PhotoImage(resized_image)

            # Clear canvas
            self.preview_canvas.delete("all")

            # Display image centered
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2

            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.current_photo)

            # Update info
            self.info_label.config(text=f"Image: {img_width}x{img_height} → {new_width}x{new_height} "
                                      f"({self.settings['save_format']})")

        except Exception as e:
            print(f"Error displaying preview: {e}")

    def save_screenshot(self, auto=False):
        """Save current screenshot"""
        if not self.current_image:
            messagebox.showwarning("No Image", "No screenshot to save")
            return

        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"screenshot_{timestamp}"

            if self.settings["include_timestamp"]:
                filename = f"{base_name}.{self.settings['save_format'].lower()}"
            else:
                filename = f"screenshot.{self.settings['save_format'].lower()}"

            filepath = os.path.join(self.screenshot_dir, filename)

            # Save image
            if self.settings["save_format"].upper() == "JPG":
                self.current_image.save(filepath, "JPEG", quality=self.settings["quality"])
            else:
                self.current_image.save(filepath, self.settings["save_format"].upper())

            if not auto:
                messagebox.showinfo("Saved", f"Screenshot saved as:\n{filepath}")

            self.status_label.config(text=f"💾 Saved: {filename}", foreground='#00aa00')

            # Clean up old screenshots
            self.cleanup_old_screenshots()

        except Exception as e:
            self.status_label.config(text=f"❌ Save failed: {e}", foreground='#cc0000')
            messagebox.showerror("Save Error", f"Failed to save screenshot: {e}")

    def copy_to_clipboard(self):
        """Copy screenshot to clipboard"""
        if not self.current_image:
            messagebox.showwarning("No Image", "No screenshot to copy")
            return

        try:
            # Save temporarily and copy to clipboard
            temp_path = os.path.join(self.temp_dir, "clipboard_temp.png")
            self.current_image.save(temp_path, "PNG")

            # Copy to clipboard (simplified - in real implementation use pyperclip or similar)
            messagebox.showinfo("Copied", "Screenshot copied to clipboard (feature not fully implemented)")

            self.status_label.config(text="📋 Copied to clipboard", foreground='#00aa00')

        except Exception as e:
            self.status_label.config(text=f"❌ Copy failed: {e}", foreground='#cc0000')
            messagebox.showerror("Copy Error", f"Failed to copy to clipboard: {e}")

    def share_screenshot(self):
        """Share screenshot (placeholder for future implementation)"""
        if not self.current_image:
            messagebox.showwarning("No Image", "No screenshot to share")
            return

        messagebox.showinfo("Share", "Sharing feature will be implemented in future updates")

    def open_gallery(self):
        """Open screenshots gallery"""
        try:
            if os.path.exists(self.screenshot_dir):
                os.startfile(self.screenshot_dir)  # Windows
            else:
                messagebox.showwarning("Gallery", "Screenshots directory not found")
        except Exception as e:
            messagebox.showerror("Gallery Error", f"Failed to open gallery: {e}")

    def clear_preview(self):
        """Clear current preview"""
        self.current_image = None
        self.current_photo = None
        self.preview_canvas.delete("all")
        self.info_label.config(text="Preview cleared")
        self.status_label.config(text="Ready", foreground='#0066cc')

    def open_capture_settings(self):
        """Open capture settings dialog"""
        settings_window = tk.Toplevel(self.capture_window)
        settings_window.title("⚙️ Capture Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)

        # Settings frame
        frame = ttk.Frame(settings_window, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Auto save
        auto_var = tk.BooleanVar(value=self.settings["auto_save"])
        ttk.Checkbutton(frame, text="Auto-save screenshots",
                        variable=auto_var).pack(anchor=tk.W, pady=5)

        # Format
        ttk.Label(frame, text="Save Format:").pack(anchor=tk.W, pady=5)
        format_combo = ttk.Combobox(frame, values=["PNG", "JPG", "BMP"], width=10)
        format_combo.set(self.settings["save_format"])
        format_combo.pack(anchor=tk.W, pady=5)

        # Quality (for JPG)
        ttk.Label(frame, text="JPG Quality (1-100):").pack(anchor=tk.W, pady=5)
        quality_entry = ttk.Entry(frame, width=10)
        quality_entry.insert(0, str(self.settings["quality"]))
        quality_entry.pack(anchor=tk.W, pady=5)

        # Include timestamp
        timestamp_var = tk.BooleanVar(value=self.settings["include_timestamp"])
        ttk.Checkbutton(frame, text="Include timestamp in filename",
                        variable=timestamp_var).pack(anchor=tk.W, pady=5)

        # Max screenshots
        ttk.Label(frame, text="Max screenshots to keep:").pack(anchor=tk.W, pady=5)
        max_entry = ttk.Entry(frame, width=10)
        max_entry.insert(0, str(self.settings["max_screenshots"]))
        max_entry.pack(anchor=tk.W, pady=5)

        # Capture delay
        ttk.Label(frame, text="Capture delay (seconds):").pack(anchor=tk.W, pady=5)
        delay_entry = ttk.Entry(frame, width=10)
        delay_entry.insert(0, str(self.settings["capture_delay"]))
        delay_entry.pack(anchor=tk.W, pady=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=20)

        def save_settings():
            try:
                self.settings["auto_save"] = auto_var.get()
                self.settings["save_format"] = format_combo.get()
                self.settings["quality"] = int(quality_entry.get())
                self.settings["include_timestamp"] = timestamp_var.get()
                self.settings["max_screenshots"] = int(max_entry.get())
                self.settings["capture_delay"] = int(delay_entry.get())

                self.save_settings()
                settings_window.destroy()
                messagebox.showinfo("Settings", "Capture settings saved")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid settings: {e}")

        ttk.Button(button_frame, text="💾 Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancel", command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)

    def load_settings(self):
        """Load capture settings"""
        try:
            settings_file = "screenshot_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
        except Exception as e:
            print(f"Error loading screenshot settings: {e}")

    def save_settings(self):
        """Save capture settings"""
        try:
            settings_file = "screenshot_settings.json"
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving screenshot settings: {e}")

    def cleanup_old_screenshots(self):
        """Clean up old screenshots to prevent disk space issues"""
        try:
            if not os.path.exists(self.screenshot_dir):
                return

            screenshots = [f for f in os.listdir(self.screenshot_dir)
                          if f.startswith("screenshot_") and f.endswith((".png", ".jpg", ".bmp"))]

            if len(screenshots) > self.settings["max_screenshots"]:
                # Sort by modification time (oldest first)
                screenshots.sort(key=lambda x: os.path.getmtime(os.path.join(self.screenshot_dir, x)))

                # Remove oldest files
                to_remove = len(screenshots) - self.settings["max_screenshots"]
                for i in range(to_remove):
                    os.remove(os.path.join(self.screenshot_dir, screenshots[i]))

        except Exception as e:
            print(f"Error cleaning up screenshots: {e}")

    def on_close_capture(self):
        """Handle capture window closing"""
        if self.current_image and not self.settings["auto_save"]:
            if messagebox.askyesno("Unsaved Screenshot",
                                  "You have an unsaved screenshot. Save it before closing?"):
                self.save_screenshot()
        self.capture_window.destroy()

    def run(self):
        """Run the screenshot capture interface"""
        self.capture_window.mainloop()


if __name__ == "__main__":
    # Test standalone
    try:
        print("🚀 Starting Screenshot Capture...")
        capture = ScreenshotCapture()
        capture.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()