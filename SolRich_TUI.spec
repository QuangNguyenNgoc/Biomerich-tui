# -*- mode: python ; coding: utf-8 -*-
# SolRich_TUI — PyInstaller spec for Terminal UI version.
from PyInstaller.utils.hooks import collect_submodules

datas = [('core/aura_catalog.json', 'core')]
binaries = []
hiddenimports = []

# Textual and Rich need their submodules collected
hiddenimports += collect_submodules('textual')
hiddenimports += collect_submodules('rich')


a = Analysis(
    ['main_tui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy', 'eel', 'gevent',
        # Web UI deps no longer needed
        'fastapi', 'uvicorn', 'websockets', 'webview', 'pywebview',
        # Deprecated modules
        'core.limbo', 'core.limbo_paths',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SolRich_TUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # TUI needs a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

