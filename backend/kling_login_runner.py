import asyncio
import logging
from datetime import datetime

from settings_store import save

LOGIN_URL = 'https://klingai.com/app/membership/membership-plan?f=1'
LOGIN_SUCCESS_SELECTOR = '.user-profile .avatar-container img[src]'
LOGIN_POLL_INTERVAL = 2
LOGIN_TIMEOUT = 300

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('kling_login')


async def run_login():
    from playwright.async_api import async_playwright

    log.info('启动 Chromium 浏览器...')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        log.info('浏览器已启动')

        async def on_console(msg):
            if msg.type in ('error', 'warning'):
                log.debug('[浏览器控制台 %s] %s', msg.type, msg.text)

        page.on('console', on_console)

        log.info('正在打开页面: %s', LOGIN_URL)
        try:
            await page.goto(LOGIN_URL, timeout=30000)
            log.info('页面已加载，请在浏览器中完成登录...')
        except Exception as e:
            log.error('页面加载失败: %s', e)
            await browser.close()
            return

        log.info('等待登录成功，轮询页面元素: %s', LOGIN_SUCCESS_SELECTOR)
        elapsed = 0
        while elapsed < LOGIN_TIMEOUT:
            try:
                matched = await page.locator(LOGIN_SUCCESS_SELECTOR).count()
            except Exception as e:
                log.debug('检测登录元素失败: %s', e)
                matched = 0

            if matched > 0:
                log.info('检测到登录成功元素，准备保存 cookies')
                break

            elapsed += LOGIN_POLL_INTERVAL
            if elapsed % 10 == 0:
                log.info('尚未检测到登录成功，已等待 %ds...', elapsed)
            await asyncio.sleep(LOGIN_POLL_INTERVAL)
        else:
            log.error('等待登录超时（%ds），未检测到登录成功元素', LOGIN_TIMEOUT)
            await browser.close()
            return

        log.info('等待 10 秒让 cookies 完全写入...')
        for i in range(10, 0, -1):
            log.info('  倒计时 %ds...', i)
            await asyncio.sleep(1)

        cookies = await context.cookies()
        log.info('获取到 %d 条 cookies', len(cookies))

        save('kling_cookies', {'cookies': cookies, 'saved_at': datetime.now().isoformat()})
        log.info('Cookies 已保存到 data/settings/kling_cookies.json')

        await browser.close()
        log.info('浏览器已关闭，登录流程完成')


def main():
    asyncio.run(run_login())


if __name__ == '__main__':
    main()
