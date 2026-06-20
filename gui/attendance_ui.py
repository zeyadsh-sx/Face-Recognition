"""Tkinter dialogs for extended attendance features."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime
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

    def open_lecture_session(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("جلسة محاضرة")
        win.geometry("500x400")
        f = ttk.Frame(win, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        # عرض المحاضرة النشطة فقط إذا بدأتِها من الواجهة الحالية
        # (لا نعرض محاضرات نشطة موجودة مسبقًا في قاعدة البيانات)
        active = None
        if getattr(self.service, 'last_lecture_name', None):
            # تم بدء محاضرة أثناء هذه الجلسة عبر الواجهة
            active = self.db.get_active_lecture()
        if active:
            ttk.Label(f, text="🟢 محاضرة نشطة:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
            info_text = (
                f"الاسم: {active['name']}\nالمادة: {active['course_code']}\n"
                f"المحاضر: {active['instructor']}\nالشعبة: {active.get('section', '-')}\n"
                f"الوقت: {str(active['start_time'])[:19]}"
            )
            ttk.Label(f, text=info_text, foreground="green").pack(anchor=tk.W, padx=20, pady=5)
            ttk.Separator(f, orient='horizontal').pack(fill=tk.X, pady=10)

        fields = {}
        ttk.Label(f, text="بيانات محاضرة جديدة:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
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

        status = ttk.Label(f, text="", foreground="blue")
        status.pack(pady=8)

        def start():
            ok, msg = self.service.start_lecture(
                fields["name"].get().strip() or "محاضرة",
                fields["code"].get().strip(),
                fields["instructor"].get().strip(),
                fields["section"].get().strip() or None,
                int(fields["late"].get().strip() or 15),
            )
            if ok:
                status.config(text=f"✓ تم بدء المحاضرة: {msg}", foreground="green")
                win.after(1500, lambda: win.destroy())
            else:
                status.config(text=f"✗ فشل: {msg}", foreground="red")

        def end():
            ok, msg, summary = self.service.end_lecture()
            if ok:
                status.config(text=f"✓ تم إنهاء المحاضرة", foreground="green")
                totals = summary.get("board", {}).get("totals", {})
                present = totals.get("present", 0)
                absent = totals.get("absent", 0)
                late = totals.get("late", 0)
                excused = totals.get("excused", 0)
                extra_lines = []
                if summary.get("email_sent") is not None:
                    extra_lines.append(f"بريد: {summary.get('email_message', '')}")
                details = (
                    f"تم تسجيل نهاية المحاضرة.\n\n"
                    f"الحضور: {present}\n"
                    f"التأخير: {late}\n"
                    f"الغياب: {absent}\n"
                    f"معذور: {excused}\n"
                )
                if extra_lines:
                    details += "\n" + "\n".join(extra_lines)
                messagebox.showinfo("انتهاء المحاضرة", details)
                win.after(500, lambda: win.destroy())
            else:
                status.config(text=f"✗ فشل: {msg}", foreground="red")

        ttk.Button(f, text="✓ بدء المحاضرة", command=start).pack(fill=tk.X, pady=4)
        if active:
            ttk.Button(f, text="✗ إنهاء + تسجيل الغياب", command=end, width=20).pack(fill=tk.X, pady=4)
        else:
            ttk.Button(f, text="✗ إنهاء + تسجيل الغياب", command=end, state='disabled', width=20).pack(fill=tk.X, pady=4)

    def open_manual_edit(self) -> None:
        students = self.db.get_all_students_v2()
        if not students:
            messagebox.showwarning("تنبيه", "لا يوجد طلاب")
            return

        win = tk.Toplevel(self.root)
        win.title("تعديل الحضور اليدوي")
        win.geometry("600x400")

        main = ttk.Frame(win, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right = ttk.Frame(main, width=220)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollable list of students
        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        lb = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=lb.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        student_map = {}
        for s in students:
            display = f"{s.get('name')} ({s.get('student_code') or '-'}) {s.get('section') or ''}"
            lb.insert(tk.END, display)
            student_map[display] = s

        # Right side controls
        ttk.Label(right, text="الحالة:").pack(anchor=tk.W, pady=(8,2))
        status_var = tk.StringVar(value="present")
        status_cb = ttk.Combobox(right, textvariable=status_var, values=["present", "late", "absent", "excused"])
        status_cb.pack(fill=tk.X, pady=2)

        ttk.Label(right, text="سبب (اختياري):").pack(anchor=tk.W, pady=(8,2))
        reason_e = ttk.Entry(right)
        reason_e.pack(fill=tk.X, pady=2)

        def on_save():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("تنبيه", "اختاري طالباً من القائمة")
                return
            display = lb.get(sel[0])
            st = student_map.get(display)
            if not st:
                messagebox.showerror("خطأ", "طالب غير معروف")
                return
            status = status_var.get()
            reason = reason_e.get().strip() or None
            time_str = None
            if status in ("present", "late"):
                time_str = datetime.now().strftime("%H:%M:%S")
            ok, msg = self.db.set_manual_attendance_status(
                st["id"], date.today().isoformat(), status, time_str, reason=reason, lecture_id=self.service.active_lecture_id
            )
            if ok:
                messagebox.showinfo("تم", f"تم تحديث الحالة: {status}")
                if self.on_students_changed:
                    self.on_students_changed()
            else:
                messagebox.showerror("فشل", f"فشل الحفظ: {msg}")

        def on_double(ev):
            on_save()

        ttk.Button(right, text="حفظ التعديل", command=on_save).pack(fill=tk.X, pady=8)
        lb.bind("<Double-1>", on_double)

        # allow keyboard search focus
        lb.focus_set()

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
            ("البريد الإلكتروني", "email"),
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
                email=entries["email"].get().strip() or None,
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

    def open_email_settings(self) -> None:
        from core.email_service import load_email_config, save_email_config, ensure_email_config_template

        ensure_email_config_template()
        cfg = load_email_config()
        win = tk.Toplevel(self.root)
        win.title("إعدادات البريد الإلكتروني")
        win.geometry("480x520")
        f = ttk.Frame(win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)

        fields = {}
        bool_vars = {}

        # Enabled checkbox
        bool_vars["enabled"] = tk.BooleanVar(value=bool(cfg.get("enabled", False)))
        ttk.Checkbutton(f, text="Enable email notifications", variable=bool_vars["enabled"]).pack(anchor=tk.W, pady=2)

        # SMTP host and port
        ttk.Label(f, text="SMTP Host").pack(anchor=tk.W)
        e = ttk.Entry(f, width=50)
        e.insert(0, cfg.get("smtp_host", ""))
        e.pack(fill=tk.X, pady=2)
        fields["smtp_host"] = e

        ttk.Label(f, text="SMTP Port").pack(anchor=tk.W)
        e = ttk.Entry(f, width=50)
        e.insert(0, str(cfg.get("smtp_port", 587)))
        e.pack(fill=tk.X, pady=2)
        fields["smtp_port"] = e

        # TLS option
        bool_vars["use_tls"] = tk.BooleanVar(value=bool(cfg.get("use_tls", True)))
        ttk.Checkbutton(f, text="Use TLS", variable=bool_vars["use_tls"]).pack(anchor=tk.W, pady=2)

        # Credentials: use environment variables or existing config file.
        ttk.Label(
            f,
            text="Credentials are kept out of the UI for security.\nUse SMTP_USERNAME/SMTP_PASSWORD in .env or edit config/email_config.json",
            foreground="gray",
        ).pack(anchor=tk.W, pady=4)

        # From address and name
        ttk.Label(f, text="From address").pack(anchor=tk.W)
        e = ttk.Entry(f, width=50)
        e.insert(0, cfg.get("from_address", ""))
        e.pack(fill=tk.X, pady=2)
        fields["from_address"] = e

        ttk.Label(f, text="From name").pack(anchor=tk.W)
        e = ttk.Entry(f, width=50)
        e.insert(0, cfg.get("from_name", ""))
        e.pack(fill=tk.X, pady=2)
        fields["from_name"] = e

        # Admin recipients
        ttk.Label(f, text="Admin recipients (comma-separated)").pack(anchor=tk.W)
        e = ttk.Entry(f, width=50)
        e.insert(0, ",".join(cfg.get("admin_recipients", [])))
        e.pack(fill=tk.X, pady=2)
        fields["admin_recipients"] = e

        # Notification toggles
        bool_vars["notify_on_lecture_end"] = tk.BooleanVar(value=bool(cfg.get("notify_on_lecture_end", True)))
        ttk.Checkbutton(f, text="Notify on lecture end", variable=bool_vars["notify_on_lecture_end"]).pack(anchor=tk.W, pady=2)

        bool_vars["notify_students_absent"] = tk.BooleanVar(value=bool(cfg.get("notify_students_absent", False)))
        ttk.Checkbutton(f, text="Notify absent students (if email present)", variable=bool_vars["notify_students_absent"]).pack(anchor=tk.W, pady=2)

        bool_vars["notify_students_late"] = tk.BooleanVar(value=bool(cfg.get("notify_students_late", False)))
        ttk.Checkbutton(f, text="Notify late students (if email present)", variable=bool_vars["notify_students_late"]).pack(anchor=tk.W, pady=2)

        def save():
            new_cfg = {
                "enabled": bool_vars["enabled"].get(),
                "smtp_host": fields["smtp_host"].get().strip(),
                "smtp_port": int(fields["smtp_port"].get().strip() or 587),
                "use_tls": bool_vars["use_tls"].get(),
                "username": "",
                "password": "",
                "from_address": fields["from_address"].get().strip(),
                "from_name": fields["from_name"].get().strip(),
                "admin_recipients": [
                    x.strip() for x in fields["admin_recipients"].get().split(",") if x.strip()
                ],
                "notify_on_lecture_end": bool_vars["notify_on_lecture_end"].get(),
                "notify_students_absent": bool_vars["notify_students_absent"].get(),
                "notify_students_late": bool_vars["notify_students_late"].get(),
            }
            ok = save_email_config(new_cfg)
            if ok:
                self.service.email_notifier.reload_config()
                messagebox.showinfo("تم", "تم حفظ إعدادات البريد")
            else:
                messagebox.showerror("خطأ", "فشل الحفظ — تحقق من صلاحيات المجلد config")

        def test():
            ok, msg = self.service.send_test_email()
            messagebox.showinfo("اختبار", msg if ok else f"فشل: {msg}")

        ttk.Button(f, text="حفظ", command=save).pack(fill=tk.X, pady=4)
        ttk.Button(f, text="إرسال رسالة تجريبية", command=test).pack(fill=tk.X, pady=4)
        ttk.Label(
            f,
            text="Gmail: فعّل App Password من حساب Google\nأو ضع SMTP_PASSWORD في ملف .env",
            foreground="gray",
        ).pack(pady=8)

    def _quick_export_pdf(self) -> None:
        ok, result = self.service.export_report_pdf(lecture_id=self.service.active_lecture_id)
        if ok:
            messagebox.showinfo("PDF", f"تم إنشاء ملف PDF:\n{result}")
        else:
            if "reportlab" in result.lower():
                messagebox.showerror(
                    "PDF",
                    f"{result}\n\nلتثبيت ReportLab، نفّذ:\npip install reportlab",
                )
            else:
                messagebox.showerror("PDF", result)

    def send_email_report_dialog(self) -> None:
        include = messagebox.askyesno(
            "إرسال بريد",
            "هل تُرسل نسخة للطلاب (الغائب/المتأخر) إن وُجد بريدهم؟",
        )
        ok, msg = self.service.send_email_report(
            include_students=include,
            lecture_id=self.service.active_lecture_id,
        )
        if ok:
            messagebox.showinfo("بريد", msg)
        else:
            messagebox.showerror("بريد", msg)


def json_summary(summary: dict) -> str:
    t = summary.get("board", {}).get("totals", {})
    return (
        f"غياب مسجّل: {summary.get('absent_marked', 0)}\n"
        f"حاضر: {t.get('present',0)} | غائب: {t.get('absent',0)} | متأخر: {t.get('late',0)}"
    )
