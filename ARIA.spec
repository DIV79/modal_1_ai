# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('commands.json', '.'),
    ('aria_icon.ico', '.'),
    ('gemini_engine.py', '.'),
] + collect_data_files('_sounddevice_data')

hiddenimports = [
    'gemini_engine',
    'sounddevice',
    '_sounddevice_data',
    'numpy',
    'speech_recognition',
    'pyttsx3',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    'requests',
    'PIL',
    'urllib.parse',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'queue',
    'threading',
    'webbrowser',
    'subprocess',
    'json',
    'os',
    'sys',
    'shutil',
    'datetime',
    're',
    'gemini_engine',
] + collect_submodules('speech_recognition') + collect_submodules('pyttsx3')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ARIA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No black console window
    icon='aria_icon.ico',
    version_file=None,
)
