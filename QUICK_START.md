## 🚀 QUICK START GUIDE - Face Recognition Attendance System

### ⚙️ Prerequisites

- Python 3.8+ (Installed)
- MySQL Server running (e.g., via XAMPP)
- All dependencies installed ✅

---

### 📋 EASIEST WAY TO RUN

#### **Option A: Use PowerShell Scripts (RECOMMENDED)**

The scripts automatically activate the virtual environment!

**In PowerShell, navigate to the project folder and run:**

```powershell
# 1. Run the Web Dashboard
.\run_dashboard.ps1
# Then open http://localhost:5000 in your browser

# 2. Run the Desktop GUI
.\run_gui.ps1

# 3. Run the Interactive Menu
.\run_menu.ps1
```

---

#### **Option B: Use Batch Files (For CMD/PowerShell)**

**Double-click any of these:**

- `run_dashboard.bat` - Starts the web dashboard
- `run_gui.bat` - Starts the desktop GUI
- `run_menu.bat` - Starts the interactive menu

---

#### **Option C: Manual Command Line (for advanced users)**

**In PowerShell:**

```powershell
# Navigate to project
cd "c:\Users\isei7en-store\OneDrive\Documents\GitHub\Face-Recognition"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Now run any of these:
python dashboard_final.py      # Web Dashboard
python gui_basic_mysql.py       # Desktop GUI
python start_mysql_app.py       # Interactive Menu
```

---

### 🌐 Access Your Applications

| Application          | URL/Command                          | Port |
| -------------------- | ------------------------------------ | ---- |
| **Web Dashboard**    | http://localhost:5000                | 5000 |
| **Desktop GUI**      | Run `run_gui.bat` or `run_gui.ps1`   | N/A  |
| **Interactive Menu** | Run `run_menu.bat` or `run_menu.ps1` | N/A  |

---

### ✅ Verification - Everything is Working!

All dependencies are installed:

- ✅ Flask (Web framework)
- ✅ MySQL Connector (Database)
- ✅ OpenCV (Camera/Image processing)
- ✅ NumPy (Numerical computing)
- ✅ Pillow (Image handling)
- ✅ Face Recognition (Face detection)
- ✅ DeepFace (Emotion detection)

---

### 📊 System Components

1. **`dashboard_final.py`** - Web-based dashboard (Flask)
2. **`gui_basic_mysql.py`** - Desktop GUI application (Tkinter)
3. **`features_ai_advanced.py`** - AI/ML features (Face recognition, anti-spoofing, emotions)
4. **`database_core_mysql.py`** - MySQL database management
5. **`start_mysql_app.py`** - Interactive menu launcher

---

### 🛠️ Troubleshooting

**Problem: "ModuleNotFoundError: No module named 'flask'"**

- Solution: Use `.venv\Scripts\python` or activate venv first
- Use the batch/PowerShell scripts provided

**Problem: MySQL connection error**

- Make sure MySQL server is running
- Check database credentials in `database_core_mysql.py`

**Problem: Camera not working**

- Ensure camera is connected and not used by other apps
- Try restarting the application

---

### 📝 Preparation Steps

1. **Setup Database (First time only):**

   ```powershell
   .\.venv\Scripts\python setup_database_mysql.py
   ```

2. **Add Students:**
   - Place student photos in `known_faces/` folder
   - Name files with student names/IDs
   - Run GUI and click "Register Student"

3. **Start Monitoring:**
   - Run `dashboard_final.py` to see real-time stats
   - Use `gui_basic_mysql.py` to manage attendance

---

### 📞 Support

For issues, ensure:

1. MySQL is running
2. You're using the PowerShell/batch scripts
3. All files are in the project folder
4. Virtual environment is activated

---

**You're all set! 🎉 Choose an option above and start using the system.**
