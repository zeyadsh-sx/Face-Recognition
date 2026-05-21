"""
SETUP INSTRUCTIONS FOR WINDOWS USERS
======================================
This file explains how to properly set up and run the Face Recognition Attendance System
"""

# The Problem:
# When you type 'python' in PowerShell, it uses the SYSTEM Python, not the virtual environment Python
# The virtual environment Python has ALL the libraries installed

# The Solution:
# Always use one of these three methods:

# METHOD 1: PowerShell Scripts (EASIEST) ✅
# ==========================================
# Just run these commands in PowerShell:
# 
# .\run_dashboard.ps1     # Starts web dashboard at http://localhost:5000
# .\run_gui.ps1           # Starts desktop GUI
# .\run_menu.ps1          # Starts interactive menu

# METHOD 2: Batch Files (EASIEST) ✅
# ===================================
# Just double-click these files:
# 
# run_dashboard.bat       # Starts web dashboard
# run_gui.bat             # Starts desktop GUI  
# run_menu.bat            # Starts interactive menu

# METHOD 3: Manual PowerShell (if above don't work)
# ==================================================
$projectPath = "c:\Users\isei7en-store\OneDrive\Documents\GitHub\Face-Recognition"
cd $projectPath

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Now you can use 'python' command directly
python dashboard_final.py      # Web Dashboard
python gui_basic_mysql.py       # Desktop GUI
python start_mysql_app.py       # Interactive Menu

# METHOD 4: Direct venv path (always works)
# ==========================================
cd "c:\Users\isei7en-store\OneDrive\Documents\GitHub\Face-Recognition"
.\.venv\Scripts\python.exe dashboard_final.py

# VERIFY EVERYTHING IS WORKING:
# ==============================
cd "c:\Users\isei7en-store\OneDrive\Documents\GitHub\Face-Recognition"
.\.venv\Scripts\python -c "import flask, mysql.connector, cv2, numpy, PIL; print('✅ All libraries loaded!')"

# STATUS: ✅ Everything is installed and ready!
# ==============================================
# - Flask ✅
# - MySQL Connector ✅
# - OpenCV ✅
# - NumPy ✅
# - Pillow ✅
# - Face Recognition (with fallback) ✅
# - DeepFace ✅
