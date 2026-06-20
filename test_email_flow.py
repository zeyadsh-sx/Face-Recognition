from core.email_service import load_email_config, save_email_config, EmailNotifier

# Prepare a test config (DO NOT USE REAL CREDENTIALS HERE)
test_cfg = {
    "enabled": True,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True,
    "username": "example_user",
    "password": "example_pass",
    "from_address": "from@example.com",
    "from_name": "Attendance System",
    "admin_recipients": ["admin@example.com"],
    "notify_on_lecture_end": True,
    "notify_on_daily_report": True,
    "notify_students_absent": False,
    "notify_students_late": False,
}

print('Saving test config...')
ok = save_email_config(test_cfg)
print('Saved:', ok)

cfg = load_email_config()
print('Loaded config enabled:', cfg.get('enabled'))

notifier = EmailNotifier(cfg)
print('EmailNotifier.is_configured():', notifier.is_configured())

print('Attempting to send test email (expected to fail without real credentials)')
ok, msg = notifier.send_test_email()
print('send_test_email ->', ok, msg)
