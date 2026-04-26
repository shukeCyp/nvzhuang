import logging
import os
import threading
import uuid
from logging.handlers import TimedRotatingFileHandler

from runtime_env import data_dir

DATA_DIR = data_dir()
LOG_DIR = os.path.join(DATA_DIR, 'log')

_LOG_LOCK = threading.Lock()
_LOG_ENTRIES = []
_LOG_SEQ = 0


class ChineseFormatter(logging.Formatter):
    LEVEL_MAP = {
        'DEBUG': '调试',
        'INFO': '信息',
        'WARNING': '警告',
        'ERROR': '错误',
        'CRITICAL': '严重',
    }

    def format(self, record):
        original_level = record.levelname
        record.levelname = self.LEVEL_MAP.get(record.levelname, record.levelname)
        try:
            return super().format(record)
        finally:
            record.levelname = original_level


class InMemoryLogHandler(logging.Handler):
    def emit(self, record):
        global _LOG_SEQ
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        with _LOG_LOCK:
            _LOG_SEQ += 1
            _LOG_ENTRIES.append({'id': _LOG_SEQ, 'line': message})
            if len(_LOG_ENTRIES) > 2000:
                del _LOG_ENTRIES[: len(_LOG_ENTRIES) - 2000]


def setup():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, 'app.log')
    file_handler = TimedRotatingFileHandler(
        log_file, when='midnight', backupCount=10, encoding='utf-8'
    )
    file_handler.suffix = '%Y-%m-%d'
    stream_handler = logging.StreamHandler()
    memory_handler = InMemoryLogHandler()
    formatter = ChineseFormatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    memory_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler, memory_handler]
    )
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('webview').setLevel(logging.WARNING)


def get_recent_logs(after_id: int = 0, limit: int = 200) -> dict:
    with _LOG_LOCK:
        entries = [item for item in _LOG_ENTRIES if item['id'] > after_id]
        if limit > 0:
            entries = entries[:limit]
        last_id = _LOG_ENTRIES[-1]['id'] if _LOG_ENTRIES else 0
    return {'entries': entries, 'last_id': last_id}


def get_current_log_id() -> int:
    with _LOG_LOCK:
        return _LOG_ENTRIES[-1]['id'] if _LOG_ENTRIES else 0


def get_log_stats() -> dict:
    if not os.path.exists(LOG_DIR):
        return {'files': [], 'total_size': 0}
    files = []
    for name in sorted(os.listdir(LOG_DIR)):
        if not name.startswith('app'):
            continue
        path = os.path.join(LOG_DIR, name)
        size = os.path.getsize(path)
        files.append({'name': name, 'size': size})
    total = sum(f['size'] for f in files)
    return {'files': files, 'total_size': total}


def clear_logs():
    if not os.path.exists(LOG_DIR):
        return
    for name in os.listdir(LOG_DIR):
        if name.startswith('app'):
            os.remove(os.path.join(LOG_DIR, name))


def pack_logs(dest_dir: str) -> str:
    import zipfile, datetime
    os.makedirs(dest_dir, exist_ok=True)
    zip_name = f"logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}.zip"
    zip_path = os.path.join(dest_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name in os.listdir(LOG_DIR):
            if name.startswith('app'):
                zf.write(os.path.join(LOG_DIR, name), name)
    return zip_path
