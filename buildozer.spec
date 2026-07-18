[app]
title = WinCurl
package.name = wincurl3
package.domain = org.jason.wincurl
source.dir = .
source.include_exts = py,png,jpg,ttf,json,wav,ogg
version = 28
# (str) Icon of the application
icon.filename = icon.png

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3==3.10.14,hostpython3==3.10.14,pygame,plyer,pyjnius
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.ndk = 25b
android.api = 33
android.minapi = 24
android.allow_backup = True
android.permissions = INTERNET, VIBRATE
p4a.setup_py = false

[buildozer]
log_level = 2
android.numeric_version = 28
