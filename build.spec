# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_all, collect_submodules
import os
import glob
import sys

# Collect all PIL/Pillow modules and data
datas_pil, binaries_pil, hiddenimports_pil = collect_all('PIL')
datas_cairo, binaries_cairo, hiddenimports_cairo = collect_all('cairosvg')
datas_cairocffi, binaries_cairocffi, hiddenimports_cairocffi = collect_all('cairocffi')

# Find TCL/TK data files
import tkinter
tkinter_dir = os.path.dirname(tkinter.__file__)

# Look for tcl and tk directories in Python installation
tcl_dir = None
tk_dir = None

# Try multiple possible locations
possible_tcl_paths = [
    os.path.join(sys.prefix, 'tcl', 'tcl8.6'),
    os.path.join(sys.prefix, 'Library', 'lib', 'tcl8.6'),
    os.path.join(tkinter_dir, 'tcl8.6'),
    os.path.join(sys.base_prefix, 'tcl', 'tcl8.6'),
]

possible_tk_paths = [
    os.path.join(sys.prefix, 'tcl', 'tk8.6'),
    os.path.join(sys.prefix, 'Library', 'lib', 'tk8.6'),
    os.path.join(tkinter_dir, 'tk8.6'),
    os.path.join(sys.base_prefix, 'tcl', 'tk8.6'),
]

for path in possible_tcl_paths:
    if os.path.exists(path):
        tcl_dir = path
        print(f"Found TCL at: {tcl_dir}")
        break

for path in possible_tk_paths:
    if os.path.exists(path):
        tk_dir = path
        print(f"Found TK at: {tk_dir}")
        break

# Collect TCL/TK data - try multiple bundling approaches
tk_datas = []

# Approach 1: Bundle to root level (sometimes works better on Windows)
if tcl_dir and os.path.exists(tcl_dir):
    tk_datas.append((tcl_dir, 'tcl8.6'))
    print(f"Bundling TCL from {tcl_dir} to tcl8.6")

if tk_dir and os.path.exists(tk_dir):
    tk_datas.append((tk_dir, 'tk8.6'))
    print(f"Bundling TK from {tk_dir} to tk8.6")

# Approach 2: Also try the nested structure
if tcl_dir and os.path.exists(tcl_dir):
    tk_datas.append((tcl_dir, os.path.join('tcl', 'tcl8.6')))

if tk_dir and os.path.exists(tk_dir):
    tk_datas.append((tk_dir, os.path.join('tcl', 'tk8.6')))

if not tk_datas:
    print("WARNING: Could not find TCL/TK libraries!")
    print(f"Python prefix: {sys.prefix}")
    print(f"Tkinter dir: {tkinter_dir}")

# Find Cairo DLLs from cairo-dlls folder
cairo_dlls = []
cairo_dll_path = os.path.join(os.getcwd(), 'cairo-dlls')

if os.path.exists(cairo_dll_path):
    print(f"Found cairo-dlls folder at: {cairo_dll_path}")
    for dll_file in glob.glob(os.path.join(cairo_dll_path, '*.dll')):
        cairo_dlls.append((dll_file, '.'))
        print(f"Adding DLL: {os.path.basename(dll_file)}")
else:
    print(f"Warning: cairo-dlls folder not found at {cairo_dll_path}")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_pil + binaries_cairo + binaries_cairocffi + cairo_dlls,
    datas=datas_pil + datas_cairo + datas_cairocffi + tk_datas,
    hiddenimports=hiddenimports_pil + hiddenimports_cairo + hiddenimports_cairocffi + [
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageEnhance',
        'PIL.ImageStat',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        '_tkinter',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='WasserzeichenTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,  # Changed from '.' to None - let PyInstaller handle temp dir
    console=True,  # Keep True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
