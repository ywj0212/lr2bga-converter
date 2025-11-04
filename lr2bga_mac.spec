# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden = collect_submodules("dearpygui")

# .app의 Info.plist
plist = {
    "CFBundleName": "LR2BGA Converter",
    "CFBundleDisplayName": "LR2BGA Converter",
    "CFBundleIdentifier": "com.mirix.lr2bga",
    "CFBundleShortVersionString": "1.0.1",
    "CFBundleVersion": "1.0.1",
    "LSMinimumSystemVersion": "11.0",
    "NSHighResolutionCapable": True,
}

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[
        ("bin/ffmpeg", "bin"),
        ("bin/ffprobe", "bin"),
    ],
    datas=[
        ("i18n/*.json", "i18n"),
        ("fonts/*", "fonts"),
    ],
    hiddenimports=hidden + ["tkinter"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['resign_hook.py'],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
    optimize=1,
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
    strip=True,
    upx=False,                 # mac에서는 보통 False 권장
    console=False,             # GUI 앱
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity="Developer ID Application: ",
    entitlements_file="./entitlements.plist",
    icon=['icons/icon.icns'],
)

# ★ 여기서 .app 번들을 생성
app = BUNDLE(
    exe,
    name="LR2BGA-Converter.app",
    icon='icons/icon.icns',
    bundle_identifier="com.example.lr2bga",
    info_plist=plist,
)
