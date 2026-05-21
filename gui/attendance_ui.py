"""Tkinter dialogs for extended attendance features."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional

try:
    import face_recognition
    FR_AVAILABLE = True
except ImportError:
    FR_AVAILABLE = False

if TYPE_CHECKING:
    from core.attendance_service import AttendanceService
    from core.database_core_mysql import MySQLAttendanceDatabase


class AttendanceUI:
    def __init__(
        self,
        root: tk.Tk,
        db: "MySQLAttendanceDatabase",
        service: "AttendanceService",
        on_students_changed: Optional[Callable[[], None]] = None,
    ):
        self.root = root
        self.db = db
        self.service = service
        self.on_students_changed = on_students_changed

    def open_live_board(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("لوحة الحضور والغياب الحية")
        win.geometry("720x520")
        text = tk.Text(win, wrap=tk.WORD, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        def refresh():
            board = self.service.get_live_board()
            text.delete("1.0", tk.END)
            t = board["totals"]
            text.insert(tk.END, f"التاريخ: {board['date']}\n")
            if self.service.active_lecture_id:
                text.insert(tk.END, f"محاضرة نشطة: {self.service.active_lecture_id}\n")
            text.insert(
                tk.END,
                f"حاضر: {t['present']} | متأخر: {t['late']} | غائب: {t['absent']} | معذور: {t['excused']}\n\n",
            )
            for label, key in [
                ("=== حاضر ===", "present"),
                ("=== متأخر ===", "late"),
                ("=== غائب ===", "absent"),
                ("=== معذور ===", "excused"),
            ]:
                text.insert(tk.END, f"{label}\n")
                for s in board[key]:
                    code = s.get("student_code") or "-"
                    cin = s.get("check_in_time") or s.get("time") or "-"
                    text.insert(tk.END, f"  • {s['name']} ({code}) — {cin}\n")
                text.insert(tk.END, "\n")

        ttk.Button(win, text="تحديث", command=refresh).pack(pady=4)
        refresh()

    def open_lecture_session(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("جلسة محاضرة")
        win.geometry("400x280")
        f = ttk.Frame(win, padding=12)
        f.pack(fill=tk.BOTH, expand=True)
        fields = {}
        for label, key in [
            ("اسم المحاضرة", "name"),
            ("كود المادة", "code"),
            ("المحاضر", "instructor"),
            ("الشعبة (اختياري)", "section"),
            ("دقائق التأخير", "late"),
        ]:
            ttk.Label(f, text=label).pack(anchor=tk.W)
            e = ttk.Entry(f)
            e.pack(fill=tk.X, pady=2)
            fields[key] = e
        fields["late"].insert(0, str(self.service.lecture_late_threshold))

        status = ttk.Label(f, text="")
        status.pack(pady=8)

        def start():
            ok, msg = self.service.start_lecture(
                fields["name"].get().strip() or "محاضرة",
                fields["code"].get().strip(),
                fields["instructor"].get().strip(),
                fields["section"].get().strip() or None,
                int(fields["late"].get().strip() or 15),
            )
            status.config(text=f"{'✓' if ok else '✗'} {msg}")

        def end():
            ok, msg, summary = self.service.end_lecture()
            status.config(text=f"{'✓' if ok else '✗'} {msg}")
            if ok:
                messagebox.showinfo("انتهاء المحاضرة", json_summary(summary))

        ttk.Button(f, text="بدء المحاضرة", command=start).pack(fill=tk.X, pady=2)
        ttk.Button(f, text="إنهاء + تسجيل الغياب", command=end).pack(fill=tk.X, pady=2)

    def open_promote_unknown(self, face_capture, load_known_faces) -> None:
        import os
        import shutil
        import pickle
        from core.paths import UNKNOWN_FACES_DIR

        temps = sorted(
            [d.name for d in UNKNOWN_FACES_DIR.iterdir() if d.is_dir() and d.name.startswith("temp_")]
        )
        if not temps:
            messagebox.showinfo("مجهول", "لا توجد مجلدات temp في unknown_faces")
            return

        temp_id = simpledialog.askstring(
            "تحويل مجهول",
            f"أدخل رقم المجلد:\n{', '.join(temps[-10:])}",
            initialvalue=temps[-1],
        )
        if not temp_id or temp_id not in temps:
            return

        name = simpledialog.askstring("اسم الطالب", "الاسم الكامل:")
        if not name:
            return
        code = simpledialog.askstring("رقم جامعي", "اختياري:") or ""
        section = simpledialog.askstring("شعبة", "اختياري:") or ""

        encoding = None
        folder = UNKNOWN_FACES_DIR / temp_id
        if FR_AVAILABLE:
            for img in folder.glob("*.jpg"):
                try:
                    img_arr = face_recognition.load_image_file(str(img))
                    encs = face_recognition.face_encodings(img_arr)
                    if encs:
                        encoding = encs[0]
                        break
                except Exception:
                    continue

        sid = self.db.promote_unknown_temp_to_student(
            temp_id, name, encoding, student_code=code, section=section
        )
        if sid:
            messagebox.showinfo("تم", f"تم تسجيل {name} (ID: {sid})")
            load_known_faces()
            if self.on_students_changed:
                self.on_students_changed()
        else:
            messagebox.showerror("خطأ", "فشل التحويل")

    def open_manual_edit(self) -> None:
        students = self.db.get_all_students_v2()
        if not students:
            messagebox.showwarning("تنبيه", "لا يوجد طلاب")
            return
        names = [s["name"] for s in students]
        name = simpledialog.askstring("تعديل", f"اسم الطالب:\n{names[:5]}...")
        if not name:
            return
        st = self.db.get_student_by_name_v2(name) or self.db.get_student_by_name(name)
        if not st:
            return
        status = simpledialog.askstring(
            "الحالة",
            "present / late / absent / excused",
            initialvalue="present",
        )
        if status not in ("present", "late", "absent", "excused"):
            return
        reason = simpledialog.askstring("سبب (اختياري)", "") or ""
        ok, msg = self.db.set_manual_attendance_status(
            st["id"], date.today().isoformat(), status, reason=reason
        )
        messagebox.showinfo("نتيجة", f"{msg}" if ok else f"فشل: {msg}")

    def open_register_full(self, capture_frame_fn) -> None:
        """Register student with metadata from camera callback."""
        win = tk.Toplevel(self.root)
        win.title("تسجيل طالب (بيانات كاملة)")
        f = ttk.Frame(win, padding=12)
        f.pack()
        entries = {}
        for label, key in [
            ("الاسم *", "name"),
            ("الرقم الجامعي", "code"),
            ("الشعبة", "section"),
            ("السنة", "year"),
            ("المجموعة", "group"),
        ]:
            ttk.Label(f, text=label).grid(row=len(entries), column=0, sticky=tk.W, pady=2)
            e = ttk.Entry(f, width=30)
            e.grid(row=len(entries), column=1, pady=2)
            entries[key] = e

        def save():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showerror("خطأ", "الاسم مطلوب")
                return
            frame, enc, path = capture_frame_fn(name)
            if frame is None:
                return
            sid = self.db.add_student_with_profile(
                name,
                enc,
                path,
                student_code=entries["code"].get().strip() or None,
                section=entries["section"].get().strip() or None,
                year_level=entries["year"].get().strip() or None,
                group_name=entries["group"].get().strip() or None,
            )
            if sid:
                messagebox.showinfo("تم", f"مسجّل: {name}")
                win.destroy()
                if self.on_students_changed:
                    self.on_students_changed()
            else:
                messagebox.showerror("خطأ", "فشل الحفظ")

        ttk.Button(f, text="التقاط من الكاميرا وحفظ", command=save).grid(row=10, column=0, columnspan=2, pady=8)

    def open_schedule_manager(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("جدول الحصص")
        win.geometry("500x400")
        listbox = tk.Listbox(win)
        listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        def refresh():
            listbox.delete(0, tk.END)
            for row in self.db.get_schedule():
                days = ["إثن", "ثلا", "أرب", "خمي", "جمع", "سبت", "أحد"]
                d = days[row["day_of_week"]] if row["day_of_week"] < 7 else str(row["day_of_week"])
                listbox.insert(
                    tk.END,
                    f"{d} {row['start_time']}-{row['end_time']} | {row['course_name']} ({row.get('section') or '-'})",
                )

        def add():
            course = simpledialog.askstring("المادة", "اسم المادة:")
            if not course:
                return
            code = simpledialog.askstring("الكود", "") or ""
            section = simpledialog.askstring("شعبة", "") or ""
            day = simpledialog.askinteger("يوم", "0=Mon..6=Sun", minvalue=0, maxvalue=6) or 0
            start = simpledialog.askstring("بداية", "08:00:00") or "08:00:00"
            end = simpledialog.askstring("نهاية", "10:00:00") or "10:00:00"
            self.db.add_schedule_entry(course, code, section, day, start, end)
            refresh()

        ttk.Button(win, text="إضافة حصة", command=add).pack(pady=4)
        ttk.Button(win, text="تحديث", command=refresh).pack(pady=4)
        refresh()

    def export_report_dialog(self) -> None:
        report = self.service.export_absence_report()
        win = tk.Toplevel(self.root)
        win.title(f"تقرير {report['date']}")
        text = tk.Text(win, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, f"غائبون ({len(report['absent_list'])}):\n")
        for s in report["absent_list"]:
            text.insert(tk.END, f"  - {s['name']} ({s.get('student_code','')})\n")
        text.insert(tk.END, f"\nمتأخرون ({len(report['late_list'])}):\n")
        for s in report["late_list"]:
            text.insert(tk.END, f"  - {s['name']}\n")


def json_summary(summary: dict) -> str:
    t = summary.get("board", {}).get("totals", {})
    return (
        f"غياب مسجّل: {summary.get('absent_marked', 0)}\n"
        f"حاضر: {t.get('present',0)} | غائب: {t.get('absent',0)} | متأخر: {t.get('late',0)}"
    )
