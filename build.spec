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
    os.path.join(tkinter_dir, 'tcl'),
    os.path.join(sys.prefix, 'tcl'),
    os.path.join(sys.prefix, 'Library', 'lib', 'tcl8.6'),
]

possible_tk_paths = [
    os.path.join(tkinter_dir, 'tk'),
    os.path.join(sys.prefix, 'tk'),
    os.path.join(sys.prefix, 'Library', 'lib', 'tk8.6'),
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

# Collect TCL/TK data - bundle to tcl/tk8.6 subdirectories
tk_datas = []
if tcl_dir and os.path.exists(tcl_dir):
    tk_datas.append((tcl_dir, 'tcl/tcl8.6'))
if tk_dir and os.path.exists(tk_dir):
    tk_datas.append((tk_dir, 'tcl/tk8.6'))

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
    # Fallback: try to find Cairo DLLs in PATH
    gtk_paths = [
        r'C:\gtk\bin',
        r'C:\Program Files\GTK3-Runtime Win64\bin',
        r'C:\Program Files (x86)\GTK3-Runtime Win64\bin',
    ]
    
    for gtk_path in gtk_paths:
        if os.path.exists(gtk_path):
            dll_patterns = ['*cairo*.dll', '*pixman*.dll', '*png*.dll', '*zlib*.dll', '*freetype*.dll']
            for pattern in dll_patterns:
                for dll in glob.glob(os.path.join(gtk_path, pattern)):
                    cairo_dlls.append((dll, '.'))
            break

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
    runtime_tmpdir='.',
    console=True,  # Keep console for debugging; change to False once everything works
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add your icon path here if you have one
)