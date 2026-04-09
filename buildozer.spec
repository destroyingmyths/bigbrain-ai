[app]
title = Big Brain
package.name = bigbrain
package.domain = org.bigbrain
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,READ_SMS,RECEIVE_SMS,SEND_SMS,READ_CALL_LOG,CALL_PHONE,READ_CONTACTS,WRITE_CONTACTS,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_BACKGROUND_LOCATION,CAMERA,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,VIBRATE,POST_NOTIFICATIONS,BIND_NOTIFICATION_LISTENER_SERVICE,REQUEST_INSTALL_PACKAGES,SYSTEM_ALERT_WINDOW
android.api = 33
android.minapi = 26
android.ndk = 25c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.sdk_path = /home/user/.buildozer/android/platform/android-sdk
android.ndk_path = /home/user/.buildozer/android/platform/android-ndk-r25c
[buildozer]
log_level = 2
warn_on_root = 1
