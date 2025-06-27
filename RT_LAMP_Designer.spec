
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('test_data', 'test_data')],
    hiddenimports=[
        'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
        'PySide6.QtNetwork', 'PySide6.QtPrintSupport', 'PySide6.QtSvg',
        'rt_lamp_app.gui.app', 'rt_lamp_app.gui.main_window', 
        'rt_lamp_app.gui.widgets', 'rt_lamp_app.gui.dialogs', 
        'rt_lamp_app.gui.results_display',
        'rt_lamp_app.core', 'rt_lamp_app.core.sequence_processing',
        'rt_lamp_app.core.thermodynamics', 'rt_lamp_app.core.exceptions',
        'rt_lamp_app.design', 'rt_lamp_app.design.primer_design',
        'rt_lamp_app.design.specificity_checker', 'rt_lamp_app.design.utils',
        'rt_lamp_app.design.exceptions',
        'rt_lamp_app.advanced', 'rt_lamp_app.advanced.msa',
        'rt_lamp_app.advanced.consensus_analysis', 'rt_lamp_app.advanced.consensus_orchestrator',
        'rt_lamp_app.config', 'rt_lamp_app.logger',
        'numpy', 'pandas', 'biopython', 'openpyxl',
        'Bio', 'Bio.Seq', 'Bio.SeqIO', 'Bio.Align', 'Bio.SeqUtils',
        'shiboken6'
    ],
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
    name='RT_LAMP_Designer',
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RT_LAMP_Designer_Folder',
)
