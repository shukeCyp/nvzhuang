import os
import sys


APP_NAME = '女装助手'


def is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))


def project_root() -> str:
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(__file__))


def bundle_root() -> str:
    if is_frozen():
        return getattr(sys, '_MEIPASS', project_root())
    return project_root()


def resource_path(*parts: str) -> str:
    return os.path.join(bundle_root(), *parts)


def data_dir() -> str:
    override = os.environ.get('NVZHUANG_DATA_DIR', '').strip()
    if override:
        return override
    return os.path.join(project_root(), 'data')


def ensure_data_dir(*parts: str) -> str:
    path = os.path.join(data_dir(), *parts)
    os.makedirs(path, exist_ok=True)
    return path
