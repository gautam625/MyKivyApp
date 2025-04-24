[app]
title = MyKivyApp
package.name = mykivyapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = kivy
orientation = portrait
osx.kivy_version = 2.1.0


[buildozer]
android.sdk_path = $HOME/.buildozer/android/platform/android-sdk
android.ndk_path = $HOME/.buildozer/android/platform/android-ndk-r25b
android.api = 33
android.build_tools = 34.0.0
log_level = 2
warn_on_root = 1
