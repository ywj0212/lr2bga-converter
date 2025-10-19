# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden = collect_submodules("dearpygui")

datas = [
    ("i18n/*.json", "i18n"),
    ("fonts/*", "fonts"),
]
binaries = [
    ("bin/ffmpeg", "."),
    ("bin/ffprobe", "."),
]

# .app의 Info.plist
plist = {
    "CFBundleName": "LR2BGA Converter",
    "CFBundleDisplayName": "LR2BGA Converter",
    "CFBundleIdentifier": "com.example.lr2bga",  # 필요 시 바꾸세요
    "CFBundleShortVersionString": "1.0.0",
    "CFBundleVersion": "1.0.0",
    "LSMinimumSystemVersion": "11.0",
    "NSHighResolutionCapable": True,
}

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden + ["tkinter"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 실행 파일 (onefile 권장)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="LR2BGA-Converter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # mac에서는 보통 False 권장
    console=False,             # GUI 앱
    icon=None,                 # 아이콘 있으면 .icns 지정
    onefile=True,              # self-extract onefile
)

# ★ 여기서 .app 번들을 생성
app = BUNDLE(
    exe,
    name="LR2BGA-Converter.app",
    icon=None,                 # 아이콘 있으면 .icns 지정
    bundle_identifier="com.example.lr2bga",
    info_plist=plist,
)
