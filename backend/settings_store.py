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
