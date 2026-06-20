from core.pdf_export import export_attendance_report_pdf
from pathlib import Path

report = {
    "date": "2026-06-20",
    "totals": {"present": 2, "late": 1, "absent": 1, "excused": 0, "students": 4},
    "absent_list": [{"name": "Ali", "student_code": "S001", "section": "A", "check_in_time": None}],
    "late_list": [{"name": "Sara", "student_code": "S002", "section": "A", "check_in_time": "09:05:00"}],
    "present_list": [{"name": "Mona", "student_code": "S003", "section": "B", "check_in_time": "08:59:00"}, {"name": "Omar", "student_code": "S004", "section": "B", "check_in_time": "08:55:00"}],
    "excused_list": [],
    "generated_at": "2026-06-20T12:00:00",
}

ok, result = export_attendance_report_pdf(report)
print(ok, result)
if ok:
    print('Generated file exists:', Path(result).exists())
