# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_data_files


project_root = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
datas = collect_data_files("voice_weather")

analysis = Analysis(
    [os.path.join(project_root, "scripts", "desktop_entry.py")],
    pathex=[os.path.join(project_root, "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["webview.platforms.cocoa"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Voice Weather",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

bundle_files = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="Voice Weather",
)

app = BUNDLE(
    bundle_files,
    name="Voice Weather.app",
    icon=None,
    bundle_identifier="com.evc509.voiceweather",
    info_plist={
        "CFBundleDisplayName": "Voice Weather",
        "CFBundleName": "Voice Weather",
        "CFBundleShortVersionString": "3.2.0",
        "CFBundleVersion": "3.2.0",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "Copyright © 2026 Evc",
    },
)
