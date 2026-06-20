from core.email_service import load_email_config, save_email_config

cfg = load_email_config()
print('Before:', cfg.get('enabled'))
new = {**cfg, 'enabled': True, 'smtp_host': cfg.get('smtp_host','smtp.gmail.com')}
ok = save_email_config(new)
print('Saved ok:', ok)
print('After:', load_email_config().get('enabled'))
