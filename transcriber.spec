# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['transcriber.py'],
    pathex=[],
    binaries=[],
    datas=[('model_dir', 'model_dir'), ('icon.ico', '.'), ('silero_encoder_v5.onnx', 'faster_whisper\\assets'), ('silero_decoder_v5.onnx', 'faster_whisper\\assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Trascrittore Audio-Testo',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Trascrittore Audio-Testo'
)
