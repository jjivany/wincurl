[app]
title = WinCurl
package.name = wincurl
package.domain = org.test
# This tells Buildozer that your main.py is in the current directory
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,pygame
orientation = portrait
fullscreen = 0

[android]
# (int) Android API to use
android.api = 33
# (int) Minimum API required
android.minapi = 24
# (str) Android NDK version to use
android.ndk = 25b
# (bool) Use AndroidX
android.enable_androidx = True
