[buildozer]
# (int) log_level = 0 (silent), 1 (info), 2 (debug)
log_level = 2

[app]
title = WinCurl
package.name = wincurl
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,pygame
orientation = portrait
fullscreen = 0

[android]
android.sdk_path = /usr/local/lib/android/sdk
# (int) Android API to use
android.api = 33
# (int) Minimum API required
android.minapi = 24
# (str) Android NDK version to use
android.ndk = 28c
# (bool) Use AndroidX
android.enable_androidx = True
