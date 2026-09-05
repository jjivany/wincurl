[app]
title = WinCurl
package.name = wincurl3
package.domain = org.jason.wincurl
source.dir = .
source.include_exts = py,png,jpg,ttf,json,wav,ogg
source.exclude_patterns = setup.py, *_test.py, test_*.py, test_*.js, *.apk
source.exclude_dirs = wincurl_web, bin, wincurl_build_clean
version = 121.1
# (str) Icon of the application
icon.filename = icon.png

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3==3.10.14,hostpython3==3.10.14,pygame_ce,plyer,pyjnius
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.ndk = 25b
android.api = 33
android.minapi = 24
android.allow_backup = True
android.permissions = INTERNET, VIBRATE
p4a.setup_py = false
p4a.local_recipes = ./p4a-recipes
ios.codesign.allowed = False

ios.ios_deploy_url = https://github.com/ios-control/ios-deploy
ios.ios_deploy_branch = 1.12.2

[buildozer]
log_level = 2
android.numeric_version = 120
