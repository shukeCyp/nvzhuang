import logging
import requests

from generators import BaseImageGenerator
from gemini_image_utils import save_generated_image
from settings_store import load

log = logging.getLogger(__name__)


class HotangImageGenerator(BaseImageGenerator):
    """荷塘图片生成器，基于 flow2api 的 OpenAI 兼容 chat completions 接口。"""

    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None):
        settings = load('hotang')
        self.base_url = (base_url or settings.get('base_url') or '').strip()
        self.model = (model or settings.get('model') or '').strip()
        self.api_key = (api_key or settings.get('api_key') or '').strip()

    def generate(
        self,
        prompt: str,
        image_b64: str,
        mime_type: str,
        output_dir: str | None = None,
    ) -> str:
        if not self.base_url:
            raise ValueError('未配置荷塘 Base URL')
        if not self.model:
            raise ValueError('未配置荷塘模型')
        if not self.api_key:
            raise ValueError('未配置荷塘 API Key')
        if not prompt or not prompt.strip():
            raise ValueError('提示词不能为空')
        if not image_b64:
            raise ValueError('荷塘图生图需要上传参考图')
        if not mime_type:
            raise ValueError('参考图 MIME 类型不能为空')

        api_url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': f'{prompt.strip()}\n\n比例固定为 9:16。'},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:{mime_type};base64,{image_b64}',
                            },
                        },
                    ],
                }
            ],
            'stream': False,
        }
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        log.info('开始调用荷塘图片生成，模型=%s，请求接口=%s', self.model, api_url)
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=180,
        )
        response.raise_for_status()
        result = response.json()
        file_path = save_generated_image(result, provider_name='hotang', output_dir=output_dir)
        log.info('荷塘图片生成完成，文件已保存：%s', file_path)
        return file_path
