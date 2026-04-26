"""
可灵登录脚本：打开浏览器，等待登录成功后保存 cookies 到配置。
用法：python scripts/kling_login.py
依赖：pip install playwright && playwright install chromium
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from settings_store import save

LOGIN_URL = 'https://klingai.com/app/membership/membership-plan?f=1'
WATCH_PATH = '/api/user/profile_and_features'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('kling_login')


async def main():
    from playwright.async_api import async_playwright

    log.info('启动 Chromium 浏览器...')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        log.info('浏览器已启动')

        login_event = asyncio.Event()

        async def on_request(request):
            if WATCH_PATH in request.url:
                log.info('→ 请求: %s %s', request.method, request.url)

        async def on_response(response):
            if WATCH_PATH in response.url:
                log.info('← 响应: %s %s', response.status, response.url)
                if response.status == 200:
                    log.info('登录成功接口已响应，触发保存流程')
                    login_event.set()
                else:
                    log.warning('接口返回非 200，状态码: %s', response.status)

        async def on_console(msg):
            if msg.type in ('error', 'warning'):
                log.debug('[浏览器控制台 %s] %s', msg.type, msg.text)

        page.on('request', on_request)
        page.on('response', on_response)
        page.on('console', on_console)

        log.info('正在打开页面: %s', LOGIN_URL)
        try:
            await page.goto(LOGIN_URL, timeout=30000)
            log.info('页面已加载，请在浏览器中完成登录...')
        except Exception as e:
            log.error('页面加载失败: %s', e)
            await browser.close()
            return

        log.info('等待登录成功信号（监听 %s）...', WATCH_PATH)
        await login_event.wait()

        log.info('等待 10 秒让 cookies 完全写入...')
        for i in range(10, 0, -1):
            log.info('  倒计时 %ds...', i)
            await asyncio.sleep(1)

        cookies = await context.cookies()
        log.info('获取到 %d 条 cookies', len(cookies))
        for c in cookies:
            log.debug('  cookie: %s = %s... (domain=%s)', c['name'], str(c['value'])[:8], c.get('domain', ''))

        save('kling_cookies', {'cookies': cookies, 'saved_at': datetime.now().isoformat()})
        log.info('Cookies 已保存到 data/settings/kling_cookies.json')

        await browser.close()
        log.info('浏览器已关闭，登录流程完成')


if __name__ == '__main__':
    asyncio.run(main())
