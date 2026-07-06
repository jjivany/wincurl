[app]
title = WinCurl
package.name = wincurl3
package.domain = org.jason.wincurl
source.dir = .
source.include_exts = py,png,jpg,ttf,json,wav
version = 17
# Add hostpython3==3.10.14 to the list
requirements = python3==3.10.14,hostpython3==3.10.14,pygame,plyer
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
