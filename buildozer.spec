[app]
title = Big Brain AI
package.name = bigbrain
package.domain = org.bigbrain
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0.0

requirements = python3,kivy==2.3.0,pillow,requests,certifi,charset-normalizer,idna,urllib3

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = apk
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
