import json
import base64
import urllib.request
import urllib.error
from settings_store import load


def get_llm_settings() -> dict:
    s = load('llm')
    return {
        'base_url': s.get('base_url', '').rstrip('/'),
        'api_key': s.get('api_key', ''),
        'model': s.get('model', ''),
    }


def chat(messages: list, **kwargs) -> str:
    cfg = get_llm_settings()
    if not cfg['base_url'] or not cfg['model']:
        raise ValueError('LLM 未配置，请在设置中填写 base_url 和 model')

    payload = json.dumps({
        'model': cfg['model'],
        'messages': messages,
        **kwargs,
    }).encode()

    req = urllib.request.Request(
        f"{cfg['base_url']}/chat/completions",
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {cfg['api_key']}",
        },
        method='POST',
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data['choices'][0]['message']['content']


def generate_scene_prompt(image_path: str, title: str, meta: dict | None = None) -> str:
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()

    ext = image_path.rsplit('.', 1)[-1].lower()
    mime = 'image/png' if ext == 'png' else 'image/jpeg'

    detail_parts = [f'商品名称：{title}']
    if meta:
        for k, v in meta.items():
            detail_parts.append(f'{k}：{v}')
    detail = '\n'.join(detail_parts)

    messages = [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'image_url',
                    'image_url': {'url': f'data:{mime};base64,{b64}'},
                },
                {
                    'type': 'text',
                    'text': (
                        f'{detail}\n\n'
                        '根据商品主图和详情，输出一个适合该商品的拍摄场景，'
                        '要求：不超过10个字，只输出场景名称，不要标点、解释或其他内容。'
                        '示例格式：户外草地阳光'
                    ),
                },
            ],
        }
    ]
    return chat(messages)
