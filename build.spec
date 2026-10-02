# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import get_package_paths, collect_all

# 1. مسیر پلاگین‌های گرافیکی (برای رندر شدنِ آیکون‌های وکتور و خاص)
pyside6_dir = get_package_paths('PySide6')[1]
imageformats_dir = os.path.join(pyside6_dir, 'plugins', 'imageformats')

# 2. جمع‌آوری تمام پیش‌نیازهای موتور وب (برای رفع قطعیِ سفیدی صفحه نقشه معماری)
we_datas, we_binaries, we_hiddenimports = collect_all('PySide6.QtWebEngineCore')

block_cipher = None

# 🚀 برگرداندن مسیرهای مقصد دقیقاً به همان شکلی که کدهای تو انتظار دارند!
added_files = [
    ('codesaver/codesaver_icons', 'codesaver_icons'), # برگشت به حالت اصلی تو
    ('codesaver/templates', 'templates'),             # برگشت به حالت اصلی تو
    ('plugins', 'plugins'),
    ('MyTheme.json', '.'),
    ('app_icon.ico', '.'),
    ('splash.png', '.'),
    (imageformats_dir, 'PySide6/plugins/imageformats') 
] + we_datas

hidden_modules = [
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtPrintSupport',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'jedi',
    'openai',
    'sqlite3'
] + we_hiddenimports

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=we_binaries,
    datas=added_files,
    hiddenimports=hidden_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='IDE_Master_v4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='IDE_Master_v4',
)