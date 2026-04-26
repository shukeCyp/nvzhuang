import json
import os

from runtime_env import data_dir

DATA_DIR = data_dir()
SETTINGS_DIR = os.path.join(DATA_DIR, 'settings')


def _path(name: str) -> str:
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    return os.path.join(SETTINGS_DIR, f'{name}.json')


def load(name: str) -> dict:
    p = _path(name)
    if not os.path.exists(p):
        return {}
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(name: str, data: dict):
    with open(_path(name), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ('true', '1', 'yes', 'y', 'on'):
            return True
        if normalized in ('false', '0', 'no', 'n', 'off', ''):
            return False
    return default
