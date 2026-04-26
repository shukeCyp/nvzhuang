import logging

from generators import BaseImageGenerator
from gemini_image_utils import build_image_edit_payload, post_generate_content, save_generated_image
from settings_store import load

log = logging.getLogger(__name__)

MODEL_NAME = 'gemini-3.1-flash-image-preview'
QUALITY_OPTIONS = {'1K', '2K', '4K'}


class YunwuImageGenerator(BaseImageGenerator):
    """云雾图片生成器，使用固定 Gemini 模型图生图。"""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, quality: str | None = None):
        settings = load('yunwu')
        self.base_url = (base_url or settings.get('base_url') or '').strip()
        self.api_key = (api_key or settings.get('api_key') or '').strip()
        self.quality = (quality or settings.get('quality') or '1K').strip().upper()

    def generate(
        self,
        prompt: str,
        image_b64: str,
        mime_type: str,
        output_dir: str | None = None,
    ) -> str:
        if not self.base_url:
            raise ValueError('未配置云雾 Base URL')
        if not self.api_key:
            raise ValueError('未配置云雾 API Key')
        if not prompt or not prompt.strip():
            raise ValueError('提示词不能为空')
        if not image_b64:
            raise ValueError('云雾图生图需要上传参考图')
        if not mime_type:
            raise ValueError('参考图 MIME 类型不能为空')
        if self.quality not in QUALITY_OPTIONS:
            raise ValueError('云雾清晰度仅支持 1K / 2K / 4K')

        payload = build_image_edit_payload(
            prompt=prompt,
            image_b64=image_b64,
            mime_type=mime_type,
            aspect_ratio='9:16',
            image_size=self.quality,
        )
        result = post_generate_content(
            base_url=self.base_url,
            model=MODEL_NAME,
            api_key=self.api_key,
            payload=payload,
        )
        file_path = save_generated_image(result, provider_name='yunwu', output_dir=output_dir)
        log.info('云雾图片生成完成，文件已保存：%s', file_path)
        return file_path
