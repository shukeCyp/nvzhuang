import base64
import io
import os
import uuid
from datetime import datetime

from PIL import Image
from runtime_env import data_dir

DATA_DIR = data_dir()
DEBUG_DIR = os.path.join(DATA_DIR, 'debug_images')


def split_image_to_quadrants(image_b64: str, mime_type: str, output_dir: str | None = None) -> list[dict]:
    if not image_b64:
        raise ValueError('缺少图片数据')

    image_bytes = base64.b64decode(image_b64)
    with Image.open(io.BytesIO(image_bytes)) as image:
        source = image.convert('RGB')
        width, height = source.size
        mid_x = width // 2
        mid_y = height // 2
        boxes = [
            (0, 0, mid_x, mid_y),
            (mid_x, 0, width, mid_y),
            (0, mid_y, mid_x, height),
            (mid_x, mid_y, width, height),
        ]

        root = output_dir or DEBUG_DIR
        if output_dir:
            save_dir = root
        else:
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            save_dir = os.path.join(root, f'split_{stamp}_{uuid.uuid4().hex[:8]}')
        os.makedirs(save_dir, exist_ok=True)

        parts = []
        for index, box in enumerate(boxes, start=1):
            piece = source.crop(box)
            file_path = os.path.join(save_dir, f'part_{index}.png')
            piece.save(file_path, format='PNG')
            with open(file_path, 'rb') as handle:
                b64 = base64.b64encode(handle.read()).decode()
            parts.append({
                'index': index,
                'path': file_path,
                'b64': b64,
                'ext': 'png',
                'mime_type': 'image/png',
                'width': piece.size[0],
                'height': piece.size[1],
            })

    return parts
