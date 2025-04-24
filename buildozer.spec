[app]
title = MyKivyApp
package.name = mykivyapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy
orientation = portrait
osx.kivy_version = 2.1.0

[buildozer]
log_level = 2
warn_on_root = 1

[app]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 24
android.build_tools = 34.0.0
android.arch = armeabi-v7a
