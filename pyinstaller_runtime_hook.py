import os
import sys


if getattr(sys, 'frozen', False):
    bundle_root = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    browsers_path = os.path.join(bundle_root, 'ms-playwright')
    if os.path.isdir(browsers_path):
        os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', browsers_path)
