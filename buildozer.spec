[app]
title = Insta Analyzer
package.name = instaanalyzer
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,ttf
version = 1.0
requirements = 
    python3,
    kivy==2.1.0,
    kivymd==1.1.1,
    requests,
    beautifulsoup4,
    android,
    pyjnius,
    openssl,
    certifi,
    chardet,
    idna,
    urllib3

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 30
android.minapi = 21
android.ndk = 23b
android.arch = armeabi-v7a
p4a.branch = develop
orientation = portrait
fullscreen = 0
