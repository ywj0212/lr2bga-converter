# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# 숨은 모듈(특히 dearpygui 내부 서브모듈) 수집
hidden = collect_submodules("dearpygui")

# 데이터/바이너리 경로
datas = [
    ("./i18n/*.json", "i18n"),
    ("./fonts/*", "fonts"),
]
binaries = [
    ("./bin/ffmpeg.exe", "."),
    ("./bin/ffprobe.exe", "."),
]

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden + ["tkinter"],  # 파일선택 대화상자 대비
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    upx=True,
    console=False,             # 콘솔 숨김 (GUI 앱)
    icon=['icons\\icon.ico'],  # 아이콘 있으면 경로 지정 (예: "assets/app.ico")
    # onefile 빌드
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
