# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


ROOT = Path.cwd()
BACKEND_DIR = ROOT / 'backend'
DATA_SETTINGS_DIR = ROOT / 'data' / 'settings'


def add_tree_if_exists(source: Path, destination: str):
    if not source.exists():
        return []
    return [(str(source), destination)]


datas = []
datas += add_tree_if_exists(BACKEND_DIR / 'vue', 'backend/vue')
datas += add_tree_if_exists(ROOT / 'ms-playwright', 'ms-playwright')

for settings_name in (
    'crawl.json',
    'global.json',
    'hotang.json',
    'kling.json',
    'llm.json',
    'prompts.json',
    'yunwu.json',
):
    settings_path = DATA_SETTINGS_DIR / settings_name
    if settings_path.exists():
        datas.append((str(settings_path), 'data/settings'))

datas += collect_data_files('playwright')
datas += copy_metadata('playwright')

hiddenimports = []
hiddenimports += collect_submodules('playwright')
hiddenimports += collect_submodules('webview')
hiddenimports += ['playwright.async_api', 'playwright.sync_api']


a = Analysis(
    ['backend/main.py'],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / 'pyinstaller_runtime_hook.py')],
    excludes=[],
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
    exclude_binaries=False,
    name='女装助手',
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
