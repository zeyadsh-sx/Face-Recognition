"""SMTP email notifications for attendance reports."""
from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.paths import CONFIG_DIR, PROJECT_ROOT

EMAIL_CONFIG_FILE = CONFIG_DIR / "email_config.json"
EMAIL_CONFIG_EXAMPLE = CONFIG_DIR / "email_config.example.json"

DEFAULT_EMAIL_CONFIG = {
    "enabled": False,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True,
    "username": "",
    "password": "",
    "from_address": "",
    "from_name": "نظام الحضور والغياب",
    "admin_recipients": [],
    "notify_on_lecture_end": True,
    "notify_on_daily_report": True,
    "notify_students_absent": False,
    "notify_students_late": False,
    "subject_prefix": "[حضور]",
}


def load_email_config() -> Dict:
    ensure_email_config_template()
    config = dict(DEFAULT_EMAIL_CONFIG)
    if EMAIL_CONFIG_FILE.exists():
        try:
            with open(EMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except (OSError, json.JSONDecodeError):
            pass
    env_password = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_PASSWORD")
    if env_password:
        config["password"] = env_password
    if os.getenv("SMTP_USERNAME"):
        config["username"] = os.getenv("SMTP_USERNAME")
    if os.getenv("SMTP_FROM"):
        config["from_address"] = os.getenv("SMTP_FROM")
    return config


def save_email_config(config: Dict) -> bool:
    ensure_email_config_template()
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        to_save = {**load_email_config(), **config}
        if to_save.get("password") in ("", "********"):
            existing = load_email_config()
            to_save["password"] = existing.get("password", "")
        with open(EMAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def ensure_email_config_template() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not EMAIL_CONFIG_EXAMPLE.exists():
        example = {
            **DEFAULT_EMAIL_CONFIG,
            "_help": {
                "gmail": "smtp.gmail.com:587, use App Password",
                "env": "Set SMTP_PASSWORD in .env instead of saving password in JSON",
            },
        }
        with open(EMAIL_CONFIG_EXAMPLE, "w", encoding="utf-8") as f:
            json.dump(example, f, ensure_ascii=False, indent=2)
    if not EMAIL_CONFIG_FILE.exists():
        with open(EMAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_EMAIL_CONFIG, f, ensure_ascii=False, indent=2)


def _format_student_lines(students: List[Dict], fields: Optional[List[str]] = None) -> str:
    if not students:
        return "  (لا يوجد)\n"
    lines = []
    for s in students:
        code = s.get("student_code") or "-"
        section = s.get("section") or ""
        email = s.get("email") or ""
        extra = f" | {section}" if section else ""
        if fields and "email" in fields and email:
            extra += f" | {email}"
        lines.append(f"  • {s.get('name', '?')} ({code}){extra}\n")
    return "".join(lines)


def build_report_html(report: Dict, lecture_name: Optional[str] = None) -> Tuple[str, str]:
    """Return (plain_text, html_body)."""
    t = report.get("totals", {})
    date_str = report.get("date", "")
    title = f"تقرير حضور — {date_str}"
    if lecture_name:
        title += f" — {lecture_name}"

    absent = report.get("absent_list", [])
    late = report.get("late_list", [])
    present = report.get("present_list", [])
    excused = report.get("excused_list", [])

    plain = (
        f"{title}\n"
        f"{'=' * 40}\n"
        f"حاضر: {t.get('present', 0)} | متأخر: {t.get('late', 0)} | "
        f"غائب: {t.get('absent', 0)} | معذور: {t.get('excused', 0)}\n\n"
        f"--- غائبون ({len(absent)}) ---\n{_format_student_lines(absent)}"
        f"\n--- متأخرون ({len(late)}) ---\n{_format_student_lines(late)}"
        f"\n--- حاضرون ({len(present)}) ---\n{_format_student_lines(present[:30])}"
    )
    if len(present) > 30:
        plain += f"  ... و {len(present) - 30} آخرين\n"

    html = f"""
    <html dir="rtl"><body style="font-family: Arial, sans-serif;">
    <h2>{title}</h2>
    <table border="1" cellpadding="8" style="border-collapse:collapse;">
    <tr><td>حاضر</td><td>{t.get('present', 0)}</td></tr>
    <tr><td>متأخر</td><td>{t.get('late', 0)}</td></tr>
    <tr><td>غائب</td><td>{t.get('absent', 0)}</td></tr>
    <tr><td>معذور</td><td>{t.get('excused', 0)}</td></tr>
    </table>
    <h3>غائبون</h3><ul>{''.join(f"<li>{s.get('name')} ({s.get('student_code','')})</li>" for s in absent) or '<li>لا يوجد</li>'}</ul>
    <h3>متأخرون</h3><ul>{''.join(f"<li>{s.get('name')} ({s.get('student_code','')})</li>" for s in late) or '<li>لا يوجد</li>'}</ul>
    <p style="color:#666;font-size:12px;">مُولّد تلقائياً — نظام التعرف على الوجه</p>
    </body></html>
    """
    return plain, html


class EmailNotifier:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_email_config()

    def reload_config(self) -> None:
        self.config = load_email_config()

    def is_configured(self) -> bool:
        c = self.config
        return bool(
            c.get("enabled")
            and c.get("smtp_host")
            and c.get("username")
            and (c.get("password") or os.getenv("SMTP_PASSWORD"))
            and c.get("from_address")
            and c.get("admin_recipients")
        )

    def _all_recipients(self, report: Dict, include_students: bool = False) -> List[str]:
        recipients = list(self.config.get("admin_recipients") or [])
        if not include_students:
            return [e.strip() for e in recipients if e and "@" in e]

        notify_absent = self.config.get("notify_students_absent", False)
        notify_late = self.config.get("notify_students_late", False)
        for s in report.get("absent_list", []):
            if notify_absent and s.get("email"):
                recipients.append(s["email"])
        for s in report.get("late_list", []):
            if notify_late and s.get("email"):
                recipients.append(s["email"])
        seen = set()
        unique = []
        for e in recipients:
            e = e.strip()
            if e and "@" in e and e.lower() not in seen:
                seen.add(e.lower())
                unique.append(e)
        return unique

    def send_mail(
        self,
        recipients: List[str],
        subject: str,
        plain_body: str,
        html_body: Optional[str] = None,
    ) -> Tuple[bool, str]:
        if not recipients:
            return False, "لا يوجد مستلمون"
        if not self.is_configured():
            return False, "إعدادات البريد غير مكتملة — راجع config/email_config.json"

        c = self.config
        prefix = c.get("subject_prefix", "[حضور]")
        full_subject = f"{prefix} {subject}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = full_subject
        msg["From"] = f"{c.get('from_name', '')} <{c['from_address']}>"
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if c.get("use_tls", True):
                with smtplib.SMTP(c["smtp_host"], int(c.get("smtp_port", 587)), timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                    server.login(c["username"], c["password"])
                    server.sendmail(c["from_address"], recipients, msg.as_string())
            else:
                with smtplib.SMTP_SSL(c["smtp_host"], int(c.get("smtp_port", 465)), timeout=30) as server:
                    server.login(c["username"], c["password"])
                    server.sendmail(c["from_address"], recipients, msg.as_string())
            return True, f"تم الإرسال إلى {len(recipients)} مستلم"
        except smtplib.SMTPAuthenticationError:
            return False, "فشل المصادقة — تحقق من البريد وكلمة مرور التطبيق (App Password)"
        except Exception as e:
            return False, f"خطأ إرسال: {e}"

    def send_attendance_report(
        self,
        report: Dict,
        lecture_name: Optional[str] = None,
        include_student_emails: bool = False,
    ) -> Tuple[bool, str]:
        self.reload_config()
        if not self.config.get("enabled"):
            return False, "البريد معطّل في الإعدادات"

        recipients = self._all_recipients(report, include_students=include_student_emails)
        plain, html = build_report_html(report, lecture_name)
        return self.send_mail(recipients, f"تقرير {report.get('date', '')}", plain, html)

    def send_test_email(self) -> Tuple[bool, str]:
        self.reload_config()
        recipients = [e.strip() for e in (self.config.get("admin_recipients") or []) if "@" in e.strip()]
        if not recipients:
            return False, "أضف بريد المشرف في admin_recipients"
        plain = "رسالة تجريبية من نظام حضور وغياب الطلاب.\nإذا وصلتك هذه الرسالة، الإعدادات صحيحة."
        html = "<html dir='rtl'><body><p>رسالة تجريبية — نظام الحضور يعمل بنجاح.</p></body></html>"
        return self.send_mail(recipients, "اختبار الإعداد", plain, html)
