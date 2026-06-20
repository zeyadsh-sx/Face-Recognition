"""Export attendance reports to PDF."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.paths import PROJECT_ROOT, REPORTS_DIR

_FONT_NAME = "AttendanceFont"
_FONT_REGISTERED = False


def _register_font() -> str:
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return _FONT_NAME
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return "Helvetica"

    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\tahoma.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        PROJECT_ROOT / "web" / "frontend" / "Inter" / "static" / "Inter-Regular.ttf",
    ]
    for path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(_FONT_NAME, str(path)))
                _FONT_REGISTERED = True
                return _FONT_NAME
            except Exception:
                continue
    return "Helvetica"


def _student_rows(students: List[Dict], time_key: str = "check_in_time") -> List[List[str]]:
    rows = []
    for i, s in enumerate(students, 1):
        t = s.get(time_key) or s.get("time") or "-"
        if hasattr(t, "isoformat"):
            t = str(t)
        rows.append([
            str(i),
            str(s.get("name", "")),
            str(s.get("student_code") or "-"),
            str(s.get("section") or "-"),
            str(t)[:8],
        ])
    return rows


def export_attendance_report_pdf(
    report: Dict,
    output_path: Optional[Path] = None,
    lecture_name: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Generate PDF from export_absence_report() dict.
    Returns (success, file_path_or_error_message).
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        return False, "ReportLab غير مثبت. ثبّت الحزمة الصحيحة باستخدام: pip install reportlab"

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = report.get("date", datetime.now().strftime("%Y-%m-%d"))
    if output_path is None:
        suffix = f"_{lecture_name[:20].replace(' ', '_')}" if lecture_name else ""
        safe_suffix = "".join(c if c.isalnum() or c in "_-" else "_" for c in suffix)
        output_path = REPORTS_DIR / f"attendance_{date_str}{safe_suffix}.pdf"
    else:
        output_path = Path(output_path)

    font = _register_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleAr",
        parent=styles["Heading1"],
        fontName=font,
        fontSize=16,
        alignment=1,
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        "NormalAr",
        parent=styles["Normal"],
        fontName=font,
        fontSize=11,
        alignment=2,
        leading=14,
    )
    section_style = ParagraphStyle(
        "SectionAr",
        parent=styles["Heading2"],
        fontName=font,
        fontSize=13,
        alignment=2,
        spaceBefore=10,
        spaceAfter=6,
    )

    title = f"Attendance Report - {date_str}"
    if lecture_name:
        title += f"\n{lecture_name}"

    t = report.get("totals", {})
    summary_text = (
        f"Present: {t.get('present', 0)} | "
        f"Late: {t.get('late', 0)} | "
        f"Absent: {t.get('absent', 0)} | "
        f"Excused: {t.get('excused', 0)} | "
        f"Total students: {t.get('students', 0)}"
    )
    generated = report.get("generated_at", datetime.now().isoformat())[:19]

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    elements = []
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Paragraph(f"تاريخ التوليد: {generated}", normal_style))
    elements.append(Spacer(1, 0.4 * cm))

    header = ["#", "Name", "ID", "Section", "Time"]
    col_widths = [1 * cm, 5.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm]

    sections = [
        ("Absent", report.get("absent_list", [])),
        ("Late", report.get("late_list", [])),
        ("Present", report.get("present_list", [])),
        ("Excused", report.get("excused_list", [])),
    ]

    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])

    for section_title, students in sections:
        elements.append(Paragraph(f"{section_title} ({len(students)})", section_style))
        body = _student_rows(students)
        if not body:
            body = [["-", "None", "-", "-", "-"]]
        tbl = Table([header] + body, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(table_style)
        elements.append(tbl)
        elements.append(Spacer(1, 0.3 * cm))

    try:
        doc.build(elements)
        return True, str(output_path.resolve())
    except Exception as e:
        return False, f"فشل إنشاء PDF: {e}"
