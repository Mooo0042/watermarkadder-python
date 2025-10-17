# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all PIL/Pillow modules and data
datas_pil, binaries_pil, hiddenimports_pil = collect_all('PIL')
datas_cairo, binaries_cairo, hiddenimports_cairo = collect_all('cairosvg')
datas_cairocffi, binaries_cairocffi, hiddenimports_cairocffi = collect_all('cairocffi')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_pil + binaries_cairo + binaries_cairocffi,
    datas=datas_pil + datas_cairo + datas_cairocffi,
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