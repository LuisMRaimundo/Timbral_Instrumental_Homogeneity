# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Timbral Instrumental Homogeneity (Gradio H_TI UI).

Build from repository root (see packaging/windows/README.md):
  pyinstaller packaging/windows/homogeneity_analyser_win.spec

Adjust hiddenimports / datas if the frozen app fails with ImportError or
missing JSON/YAML at runtime (music21 and Gradio are heavy trees).
"""
import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Directory containing this .spec file (…/packaging/windows)
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
# Repository root (parent of packaging/)
REPO_ROOT = os.path.abspath(os.path.join(SPEC_DIR, "..", ".."))
SRC = os.path.join(REPO_ROOT, "src")

datas = []
datas += collect_data_files("homogeneity_analyser.acoustic_profiles")
# Gradio: collect non-.py assets; .py modules must live on disk (see module_collection_mode) so
# gradio.component_meta can read sibling sources via inspect.getfile().
datas += collect_data_files("gradio")
datas += collect_data_files("gradio_client")
datas += collect_data_files("safehttpx")
datas += collect_data_files("groovy")
# music21: add collect_data_files / collect_submodules here if runtime tests show missing
# environment files or corpora (see packaging/windows/README.md).

hiddenimports = list(collect_submodules("homogeneity_analyser"))
# Explicit symbolic-inspection / H_TI stack (also covered by collect_submodules; listed for clarity).
hiddenimports.extend(
    m
    for m in (
        "homogeneity_analyser.services.score_audit",
        "homogeneity_analyser.ui.callbacks",
        "homogeneity_analyser.ui.gradio_app",
    )
    if m not in hiddenimports
)
# Common runtime gaps (extend as needed after first --onedir test):
_extra = [
    "gradio",
    "gradio_client",
    "uvicorn",
    "starlette",
    "fastapi",
    "pydantic",
    "anyio",
    "httpx",
    "orjson",
    "websockets",
    "music21",
    "matplotlib",
    "matplotlib.backends.backend_agg",
    "PIL",
    "kaleido",
    "plotly",
    "plotly.graph_objects",
    "pandas",
    "numpy",
    "scipy",
]
hiddenimports.extend([m for m in _extra if m not in hiddenimports])

a = Analysis(
    [os.path.join(SPEC_DIR, "frozen_launcher.py")],
    pathex=[SRC],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    module_collection_mode={
        "gradio": "py",
        "gradio_client": "py",
    },
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TimbralInstrumentalHomogeneity",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name="TimbralInstrumentalHomogeneity",
)
