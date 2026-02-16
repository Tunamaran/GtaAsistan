# -*- mode: python ; coding: utf-8 -*-
# main.spec - PyInstaller spec dosyası (Asistan/Main)

import os
PROJ = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[PROJ],
    binaries=[],
    datas=[
        ('app_icon.ico', '.'),
    ],
    hiddenimports=[
        'config', 'database', 'history', 'ui', 'workers',
        'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
        'winocr', 'pytesseract',
        'winrt', 'winrt.windows.media.ocr',
        'winrt.windows.graphics.imaging',
        'winrt.windows.storage.streams',
        'winrt.windows.globalization',
        'winrt.windows.foundation',
        'winrt.windows.foundation.collections',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'paddleocr', 'paddlepaddle', 'paddlex'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GtaAsistan_Main',
)
