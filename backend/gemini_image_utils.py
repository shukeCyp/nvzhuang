import base64
import logging
import os
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

import requests
from runtime_env import data_dir

log = logging.getLogger(__name__)

DATA_DIR = data_dir()
GENERATED_DIR = os.path.join(DATA_DIR, 'generated_images')


def build_generate_content_url(base_url: str, model: str) -> str:
    return f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent"


def build_headers(api_key: str) -> dict:
    return {
        'Authorization': f'Bearer {api_key}',
        'x-goog-api-key': api_key,
        'Content-Type': 'application/json',
    }


def build_image_edit_payload(
    prompt: str,
    image_b64: str,
    mime_type: str,
    aspect_ratio: str = '9:16',
    image_size: str | None = None,
) -> dict:
    image_config = {'aspectRatio': aspect_ratio}
    if image_size:
        image_config['imageSize'] = image_size

    return {
        'contents': [
            {
                'role': 'user',
                'parts': [
                    {
                        'inlineData': {
                            'mimeType': mime_type,
                            'data': image_b64,
                        }
                    },
                    {'text': prompt.strip()},
                ],
            }
        ],
        'generationConfig': {
            'responseModalities': ['IMAGE'],
            'imageConfig': image_config,
        },
    }


def post_generate_content(
    base_url: str,
    model: str,
    api_key: str,
    payload: dict,
    timeout: int = 180,
) -> dict:
    api_url = build_generate_content_url(base_url, model)
    log.info('开始调用 Gemini 图生图接口，模型=%s，请求接口=%s', model, api_url)
    response = requests.post(
        api_url,
        json=payload,
        headers=build_headers(api_key),
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def save_generated_image(payload: dict, provider_name: str, output_dir: str | None = None) -> str:
    image_bytes, ext = extract_image_data(payload)
    if not image_bytes:
        image_url = extract_image_url(payload)
        if image_url:
            response = requests.get(image_url, timeout=180)
            response.raise_for_status()
            image_bytes = response.content
            ext = guess_extension(image_url, response.headers.get('Content-Type', ''))
        else:
            raise ValueError(f'{provider_name} 接口返回格式不支持，未找到图片数据')

    output_root = output_dir or GENERATED_DIR
    os.makedirs(output_root, exist_ok=True)
    unique_suffix = uuid.uuid4().hex[:8]
    file_path = os.path.join(
        output_root,
        f"{provider_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{unique_suffix}{ext}",
    )
    with open(file_path, 'wb') as handle:
        handle.write(image_bytes)
    return file_path


def extract_image_data(payload: dict) -> tuple[bytes | None, str]:
    for node in iter_nodes(payload):
        if not isinstance(node, dict):
            continue
        if node.get('b64_json'):
            return base64.b64decode(node['b64_json']), '.png'
        inline_data = node.get('inlineData') or node.get('inline_data')
        if isinstance(inline_data, dict) and inline_data.get('data'):
            return (
                base64.b64decode(inline_data['data']),
                guess_extension_from_mime(inline_data.get('mimeType', 'image/png')),
            )
    return None, '.png'


def extract_image_url(payload: dict) -> str | None:
    for node in iter_nodes(payload):
        if not isinstance(node, dict):
            continue
        url = node.get('url')
        if isinstance(url, str) and looks_like_image_url(url):
            return url
        image_url = node.get('image_url')
        if isinstance(image_url, str) and looks_like_image_url(image_url):
            return image_url
        if isinstance(image_url, dict) and looks_like_image_url(image_url.get('url', '')):
            return image_url['url']

    text = extract_text_content(payload)
    if not text:
        return None

    markdown_match = re.search(r'!\[[^\]]*\]\((https?://[^)]+)\)', text)
    if markdown_match:
        return markdown_match.group(1)

    url_match = re.search(r'https?://\S+', text)
    if url_match:
        return url_match.group(0).rstrip(').,\'"')
    return None


def extract_text_content(payload: dict) -> str:
    texts = []
    for node in iter_nodes(payload):
        if isinstance(node, dict) and isinstance(node.get('content'), str):
            texts.append(node['content'])
        if isinstance(node, dict) and isinstance(node.get('text'), str):
            texts.append(node['text'])
    return '\n'.join(texts).strip()


def iter_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_nodes(child)
    elif isinstance(value, list):
        for item in value:
            yield from iter_nodes(item)


def guess_extension_from_mime(mime_type: str) -> str:
    lowered = (mime_type or '').lower()
    if 'jpeg' in lowered or 'jpg' in lowered:
        return '.jpg'
    if 'webp' in lowered:
        return '.webp'
    if 'gif' in lowered:
        return '.gif'
    return '.png'


def looks_like_image_url(value: str) -> bool:
    lowered = (value or '').lower()
    return lowered.startswith('http://') or lowered.startswith('https://')


def guess_extension(image_url: str, content_type: str) -> str:
    ext = guess_extension_from_mime(content_type)
    if ext != '.png' or 'png' in (content_type or '').lower():
        return ext

    path = urlparse(image_url).path.lower()
    for suffix in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
        if path.endswith(suffix):
            return '.jpg' if suffix == '.jpeg' else suffix
    return '.png'
