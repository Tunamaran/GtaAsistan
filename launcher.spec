# -*- mode: python ; coding: utf-8 -*-
# launcher.spec - PyInstaller spec dosyası (Launcher)

import os
PROJ = os.path.abspath('.')

a = Analysis(
    ['launcher.py'],
    pathex=[PROJ],
    binaries=[],
    datas=[
        ('gta_tum_araclar.json', '.'),
        ('app_icon.ico', '.'),
    ],
    hiddenimports=[
        'config', 'database', 'history', 'ui', 'workers', 'main',
        'VeriÇek',
        'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
        'cloudscraper', 'bs4', 'lxml',
        # OCR ve Ekran Yakalama
        'winocr', 
        'winrt.windows.media.ocr',
        'winrt.windows.graphics.imaging',
        'winrt.windows.storage.streams',
        'winrt.windows.globalization',
        'winrt.windows.foundation',
        'winrt.windows.foundation.collections',
        'mss', 'cv2', 'numpy', 'PIL', 'keyboard', 'thefuzz',
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
    name='launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='app_icon.ico',
    uac_admin=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GtaAsistan',
)
