# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs


project_root = Path(SPECPATH)
azure_speech_binaries = collect_dynamic_libs("azure.cognitiveservices.speech")

datas = [
    (str(project_root / "app" / "assets"), "app/assets"),
    (str(project_root / "docs"), "docs"),
]

hiddenimports = [
    "PyQt6.QtMultimedia",
    "PyQt6.QtNetwork",
    "azure.cognitiveservices.speech",
    "boto3",
    "google.cloud.texttospeech",
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
]

block_cipher = None

a = Analysis(
    ["app/main.py"],
    pathex=[str(project_root)],
    binaries=azure_speech_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TextToSpeech",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "app" / "assets" / "icons" / "tts.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TextToSpeech",
)
