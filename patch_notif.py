import re

with open("main.py", "r") as f:
    code = f.read()

old = '''def _check_notification_listener(callback=None):
    if not IS_ANDROID:
        if callback: callback()
        return
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        flat = android.provider.Settings.Secure.getString(
            context.getContentResolver(), "enabled_notification_listeners"
        )
        if flat and context.getPackageName() in flat:
            if callback: callback()
        else:
            _show_notif_popup(callback)
    except Exception:
        if callback: callback()'''

new = '''def _check_notification_listener(callback=None):
    if not IS_ANDROID:
        if callback: callback()
        return
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Settings = autoclass("android.provider.Settings$Secure")
        context = PythonActivity.mActivity
        flat = Settings.getString(
            context.getContentResolver(), "enabled_notification_listeners"
        )
        if flat and context.getPackageName() in flat:
            if callback: callback()
        else:
            _show_notif_popup(callback)
    except Exception:
        if callback: callback()'''

code = code.replace(old, new)
with open("main.py", "w") as f:
    f.write(code)
print("Done")
