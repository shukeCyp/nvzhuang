import asyncio
import base64
import logging
import os
import tempfile
import urllib.request

from generators import BaseVideoGenerator
from runtime_env import data_dir
from settings_store import as_bool, load

log = logging.getLogger(__name__)

QUALITY_MODE = {'720P': 'fast', '1080P': 'nice', '4K': '4k'}
VIDEO_URL = 'https://klingai.com/app/video/new?ac=1'
SUBMIT_PATH = '/api/task/submit'
FEEDS_URL = 'https://klingai.com/api/user/works/personal/feeds'
POLL_INTERVAL = 10
POLL_TIMEOUT = 600  # 最多等 10 分钟


class KlingVideoGenerator(BaseVideoGenerator):

    def __init__(self):
        s = load('kling')
        g = load('global')
        self.headless = as_bool(g.get('headless', False), default=False)
        self.model = s.get('model', '2.6')
        self.duration = int(s.get('duration', 5))
        self.quality = s.get('quality', '720P')
        self.ratio = s.get('ratio', '16:9')
        self.cookies = load('kling_cookies').get('cookies', [])

    def generate(
        self,
        image_b64: str,
        prompt: str,
        model: str | None = None,
        duration: int | None = None,
        quality: str | None = None,
        ratio: str | None = None,
        output_dir: str | None = None,
        **kwargs,
    ) -> str:
        if not self.cookies:
            raise ValueError('可灵未登录，请先在设置页面完成登录')
        return asyncio.run(self._generate(
            image_b64, prompt,
            model or self.model,
            int(duration or self.duration),
            quality or self.quality,
            ratio or self.ratio,
            output_dir,
        ))

    async def _generate(self, image_b64, prompt, model, duration, quality, ratio, output_dir):
        from playwright.async_api import async_playwright

        log.info('启动浏览器，注入 cookies...')
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            await context.add_cookies(self.cookies)
            page = await context.new_page()
            page.on('console', lambda msg: log.info('[browser] %s', msg.text))

            # 先跳转主页
            log.info('跳转主页...')
            await page.goto('https://klingai.com/app', timeout=30000)
            await asyncio.sleep(3)

            # 监听 submit 接口，拿 task_id
            task_id_future: asyncio.Future = asyncio.get_event_loop().create_future()
            feeds_data: list = []

            async def on_response(response):
                if SUBMIT_PATH in response.url and not task_id_future.done():
                    try:
                        data = await response.json()
                        tid = data.get('data', {}).get('task', {}).get('id')
                        if tid:
                            log.info('任务提交成功，task_id=%s', tid)
                            task_id_future.set_result(tid)
                    except Exception as e:
                        log.warning('解析 submit 响应失败: %s', e)
                elif FEEDS_URL.split('?')[0] in response.url:
                    try:
                        data = await response.json()
                        history = (data or {}).get('data', {}).get('history') or []
                        feeds_data.clear()
                        feeds_data.extend(history)
                    except Exception:
                        pass

            page.on('response', on_response)

            # 写入 overlay key，跳转视频生成页
            log.info('跳转视频生成页: %s', VIDEO_URL)
            await page.evaluate("localStorage.setItem('overlay-manage__auto-dialog__omni-new-function-dialog', '1777097814208')")
            await page.goto(VIDEO_URL, timeout=30000)
            await asyncio.sleep(2)

            # 跳转后写入 userPreferences，然后刷新
            await self._write_preferences(page, model, quality, duration, ratio)
            written = await page.evaluate("JSON.parse(localStorage.getItem('user') || '{}').userPreferences")
            log.info('写入验证 userPreferences=%s', written)
            await page.reload()
            await asyncio.sleep(2)
            log.info('localStorage 已更新并刷新: model=%s quality=%s duration=%s ratio=%s', model, quality, duration, ratio)

            upload_tmp_path = None
            try:
                # 通过 UI 设置参数
                await self._set_ui_params(page, model, quality, duration)

                if image_b64:
                    log.info('上传参考图片...')
                    img_bytes = base64.b64decode(image_b64)
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                        tmp_file.write(img_bytes)
                        upload_tmp_path = tmp_file.name
                    upload_input = page.locator('input[type="file"]').first
                    await upload_input.set_input_files(upload_tmp_path)
                    await asyncio.sleep(2)
                    log.info('图片已上传')

                # 填写提示词
                log.info('填写提示词: %s', prompt[:30])
                editor = page.locator('.tiptap.ProseMirror')
                await editor.click()
                await editor.fill(prompt)
                await asyncio.sleep(1)

                # 点击生成
                log.info('点击生成按钮...')
                await page.locator('button.button-pay .inner').click()

                # 等待 task_id
                log.info('等待任务提交响应...')
                task_id = await asyncio.wait_for(task_id_future, timeout=30)

                # 轮询 feeds 接口查询状态
                log.info('开始轮询任务状态，task_id=%s', task_id)
                video_url = await self._poll_task(feeds_data, task_id)
            finally:
                await browser.close()
                if upload_tmp_path and os.path.exists(upload_tmp_path):
                    os.remove(upload_tmp_path)

        # 下载视频
        log.info('下载视频: %s', video_url)
        return self._download_video(video_url, task_id, output_dir)

    async def _poll_task(self, feeds_data: list, task_id: int) -> str:
        elapsed = 0
        while elapsed < POLL_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            for item in list(feeds_data):
                if item.get('task', {}).get('id') != task_id:
                    continue
                task_status = item.get('task', {}).get('status')
                log.info('任务状态: %s (已等待 %ds)', task_status, elapsed)
                if task_status == 99:
                    for work in item.get('works', []):
                        url = work.get('resource', {}).get('resource', '')
                        if url:
                            return url
                elif task_status in (4, 50):
                    raise RuntimeError(f'任务失败，status={task_status}')
        raise TimeoutError(f'任务超时（{POLL_TIMEOUT}s），task_id={task_id}')

    @staticmethod
    def _download_video(url: str, task_id: int, output_dir: str | None) -> str:
        if not output_dir:
            output_dir = os.path.join(data_dir(), 'generated_videos')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f'kling_{task_id}.mp4')
        urllib.request.urlretrieve(url, file_path)
        log.info('视频已保存: %s', file_path)
        return file_path

    async def _set_ui_params(self, page, model, quality, duration):
        log.info('UI 设置参数: model=%s quality=%s duration=%s', model, quality, duration)

        # 1. 选择模型
        await page.locator('.el-select__wrapper').first.click()
        await asyncio.sleep(0.5)
        model_label = '视频 3.0' if model == '3.0' else '视频 2.6'
        await page.locator(f'.el-select-dropdown__item .model-name', has_text=model_label).first.click()
        await asyncio.sleep(0.5)
        log.info('模型已选择: %s', model_label)

        # 2. 取消音画同步（如果已选中）
        sync_btn = page.locator('.setting-switch').filter(has_text='音画同步')
        icon = sync_btn.locator('.svg-icon use')
        href = await icon.get_attribute('xlink:href')
        if href and 'unchecked' not in href:
            await sync_btn.click()
            await asyncio.sleep(0.3)
            log.info('已取消音画同步')

        # 3. 点击设置按钮
        await page.locator('.setting-select').first.click()
        await asyncio.sleep(0.5)

        # 4. 选择清晰度
        quality_map = {'720P': '720p', '1080P': '1080p', '4K': '4K'}
        quality_label = quality_map.get(quality, '720p')
        await page.locator('.option-tab-item.model_mode', has_text=quality_label).click()
        await asyncio.sleep(0.3)
        log.info('清晰度已选择: %s', quality_label)

        # 5. 选择时长
        if model == '2.6':
            await page.locator('.option-tab-item.duration', has_text=f'{duration}s').click()
        else:
            # 3.0 用 slider，范围 3-15
            slider = page.locator('.el-slider__button-wrapper')
            box = await slider.bounding_box()
            runway = page.locator('.el-slider__runway')
            runway_box = await runway.bounding_box()
            pct = (duration - 3) / (15 - 3)
            target_x = runway_box['x'] + runway_box['width'] * pct
            await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            await page.mouse.down()
            await page.mouse.move(target_x, box['y'] + box['height'] / 2)
            await page.mouse.up()
        await asyncio.sleep(0.3)
        log.info('时长已设置: %ss', duration)

        # 关闭弹窗（点击空白处）
        await page.keyboard.press('Escape')
        await asyncio.sleep(0.3)

    def _write_preferences(self, page, model, quality, duration, ratio):
        import asyncio
        mode = QUALITY_MODE.get(quality, 'fast')
        pref = {
            "hasVisitedKling3_0": True,
            "videoVersionSelect": model,
            "PESwitchShow": False,
            "noWatermark": True,
            "setting": {
                "image": {},
                "video": {
                    "aspectRatio": ratio,
                    "videoLength": str(duration),
                    "imageCount": 1,
                    "videoMode": mode,
                },
                "audio": {},
                "tryOn": {},
                "videoExtend": {},
                "effects": {},
            },
        }
        return page.evaluate("""(pref) => {
            let raw = localStorage.getItem('user');
            console.log('[kling] user raw:', raw ? raw.substring(0, 100) : 'NULL');
            let user = {};
            try { user = JSON.parse(raw || '{}'); } catch(e) { console.log('[kling] parse error:', e); }
            console.log('[kling] user keys:', Object.keys(user).join(','));
            user.userPreferences = pref;
            localStorage.setItem('user', JSON.stringify(user));
            let verify = JSON.parse(localStorage.getItem('user') || '{}');
            console.log('[kling] after write userPreferences:', JSON.stringify(verify.userPreferences).substring(0, 80));
            return verify.userPreferences;
        }""", pref)
