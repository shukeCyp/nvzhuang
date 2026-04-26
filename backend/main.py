import webview
import os
import logging
import threading
import uuid
import base64
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from crawler import crawl
from crawl_metadata import get_crawl_metadata
from hotang_image_generator import HotangImageGenerator
from image_util import split_image_to_quadrants
from yunwu_image_generator import YunwuImageGenerator
from settings_store import load, save
from llm_util import chat, generate_scene_prompt
from logger import setup, get_log_stats, clear_logs, pack_logs, get_current_log_id, get_recent_logs
from runtime_env import data_dir, is_frozen, resource_path

DATA_DIR = data_dir()
setup()
log = logging.getLogger(__name__)
TASK_LOCK = threading.Lock()
STATUS_LOCK = threading.Lock()
CRAWL_TASKS = {}


class Api:
    def start_crawl(self, params):
        os.makedirs(DATA_DIR, exist_ok=True)
        task_id = uuid.uuid4().hex
        initial_log_id = get_current_log_id()
        task = {
            'id': task_id,
            'status': 'running',
            'progress': 0,
            'message': '任务已创建，等待开始',
            'summary': None,
            'error': None,
            'start_log_id': initial_log_id,
        }
        with TASK_LOCK:
            CRAWL_TASKS[task_id] = task

        def update_progress(progress, message):
            with TASK_LOCK:
                current = CRAWL_TASKS.get(task_id)
                if not current:
                    return
                current['progress'] = progress
                current['message'] = message

        def run_task():
            try:
                log.info(
                    '开始抓取任务，地区=%s，分类=%s，数量=%s',
                    params.get('region'),
                    params.get('category_id'),
                    params.get('count'),
                )
                summary = crawl(
                    cookie=params.get('cookie', ''),
                    region=params.get('region', 'US'),
                    category_id=params.get('category_id', '28'),
                    count=int(params.get('count', 48)),
                    data_dir=DATA_DIR,
                    category_name=params.get('category_name'),
                    progress_callback=update_progress,
                )
                with TASK_LOCK:
                    current = CRAWL_TASKS.get(task_id)
                    if current:
                        current['status'] = 'completed'
                        current['progress'] = 100
                        current['message'] = f"抓取完成，共 {summary['total_count']} 条，保存至 {summary['save_dir']}"
                        current['summary'] = summary
                log.info('抓取任务结束，任务编号=%s', task_id)
            except Exception as e:
                log.error(f"抓取失败：{e}")
                with TASK_LOCK:
                    current = CRAWL_TASKS.get(task_id)
                    if current:
                        current['status'] = 'failed'
                        current['error'] = str(e)
                        current['message'] = f'抓取失败：{e}'

        threading.Thread(target=run_task, daemon=True).start()
        return {'ok': True, 'task_id': task_id, 'start_log_id': initial_log_id}

    def get_crawl_status(self, task_id, after_log_id=0):
        with TASK_LOCK:
            task = CRAWL_TASKS.get(task_id)
            if not task:
                return {'ok': False, 'message': '任务不存在'}
            snapshot = {
                'status': task['status'],
                'progress': task['progress'],
                'message': task['message'],
                'summary': task['summary'],
                'error': task['error'],
                'start_log_id': task['start_log_id'],
            }
        effective_after_id = max(int(after_log_id or 0), int(snapshot['start_log_id']))
        logs = get_recent_logs(after_id=effective_after_id, limit=200)
        snapshot.update({
            'ok': True,
            'logs': logs['entries'],
            'last_log_id': logs['last_id'],
        })
        return snapshot

    def get_settings(self, name):
        return load(name)

    def get_crawl_metadata(self):
        return get_crawl_metadata()

    def list_projects(self):
        projects = []
        if not os.path.isdir(DATA_DIR):
            return {'ok': True, 'projects': projects}

        for entry in os.scandir(DATA_DIR):
            if not entry.is_dir():
                continue
            summary_path = os.path.join(entry.path, 'summary.json')
            if not os.path.isfile(summary_path):
                continue
            try:
                with open(summary_path, 'r', encoding='utf-8') as handle:
                    summary = json.load(handle)
            except Exception as e:
                log.warning('读取项目摘要失败：%s, error=%s', summary_path, e)
                continue

            projects.append({
                'id': entry.name,
                'name': entry.name,
                'path': entry.path,
                'category_name': summary.get('category_name') or summary.get('category_id') or '-',
                'region': summary.get('region') or '-',
                'crawl_date': summary.get('crawl_date') or '',
                'total_count': int(summary.get('total_count') or 0),
                'image_count': int(summary.get('image_count') or 0),
                'biz_date': summary.get('biz_date') or '',
            })

        projects.sort(key=lambda item: item.get('crawl_date') or item.get('name') or '', reverse=True)
        return {'ok': True, 'projects': projects}

    def list_project_items(self, project_id):
        if not project_id:
            return {'ok': False, 'message': '项目不存在'}

        project_dir = os.path.join(DATA_DIR, project_id)
        summary_path = os.path.join(project_dir, 'summary.json')
        items_dir = os.path.join(project_dir, 'items')
        if not os.path.isdir(project_dir) or not os.path.isfile(summary_path):
            return {'ok': False, 'message': '项目不存在'}

        try:
            with open(summary_path, 'r', encoding='utf-8') as handle:
                summary = json.load(handle)
        except Exception as e:
            return {'ok': False, 'message': f'读取项目摘要失败：{e}'}

        items = []
        if os.path.isdir(items_dir):
            for entry in os.scandir(items_dir):
                if not entry.is_file() or not entry.name.endswith('.json'):
                    continue
                try:
                    with open(entry.path, 'r', encoding='utf-8') as handle:
                        item = json.load(handle)
                except Exception as e:
                    log.warning('读取商品文件失败：%s, error=%s', entry.path, e)
                    continue

                product_id = item.get('product_id') or entry.name.replace('.json', '')
                status = self._load_status(project_dir, product_id)
                items.append({
                    'product_id': product_id,
                    'title': item.get('title') or '-',
                    'price': item.get('price'),
                    'sales_count': item.get('sales_count'),
                    'rank': item.get('rank'),
                    'seller_name': item.get('seller_name') or '-',
                    'image_url': item.get('image_url') or '',
                    'gmv': item.get('gmv'),
                    'category': item.get('category') or summary.get('category_name') or '-',
                    'product_images': self._list_product_images(project_dir, product_id),
                    'role_images': status.get('role_images', []),
                    'video_url': status.get('video', ''),
                    'running': status.get('running', ''),
                })

        items.sort(key=lambda item: (item.get('rank') is None, item.get('rank') or 0))
        project = {
            'id': project_id,
            'name': project_id,
            'path': project_dir,
            'category_name': summary.get('category_name') or summary.get('category_id') or '-',
            'region': summary.get('region') or '-',
            'crawl_date': summary.get('crawl_date') or '',
            'total_count': int(summary.get('total_count') or 0),
            'image_count': int(summary.get('image_count') or 0),
            'biz_date': summary.get('biz_date') or '',
        }
        return {'ok': True, 'project': project, 'items': items}

    def _list_product_images(self, project_dir, product_id):
        image_dir = os.path.join(project_dir, 'images', str(product_id))
        if not os.path.isdir(image_dir):
            return []

        def sort_key(name):
            stem = os.path.splitext(name)[0]
            return (not stem.isdigit(), int(stem) if stem.isdigit() else stem)

        files = []
        for entry in os.scandir(image_dir):
            if not entry.is_file():
                continue
            lowered = entry.name.lower()
            if not lowered.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                continue
            files.append(entry.path)
        files.sort(key=lambda path: sort_key(os.path.basename(path)))
        return files

    def set_settings(self, name, data):
        save(name, data)
        log.info(f"设置已保存：{name}")
        return {'ok': True}

    def generate_hotang_image(self, params):
        try:
            generator = HotangImageGenerator()
            file_path = generator.generate(
                prompt=params.get('prompt', ''),
                image_b64=params.get('image_b64', ''),
                mime_type=params.get('mime_type', ''),
                output_dir=params.get('output_dir'),
            )
            return self._build_image_result(file_path)
        except Exception as e:
            log.error(f"荷塘图片生成失败：{e}")
            return {'ok': False, 'message': f'荷塘图片生成失败：{e}'}

    def generate_yunwu_image(self, params):
        try:
            generator = YunwuImageGenerator()
            file_path = generator.generate(
                prompt=params.get('prompt', ''),
                image_b64=params.get('image_b64', ''),
                mime_type=params.get('mime_type', ''),
                output_dir=params.get('output_dir'),
            )
            return self._build_image_result(file_path)
        except Exception as e:
            log.error(f"云雾图片生成失败：{e}")
            return {'ok': False, 'message': f'云雾图片生成失败：{e}'}

    def generate_image_task(self, params):
        import re
        product_id = params.get('product_id', '')
        main_image_path = params.get('main_image_path', '')
        title = params.get('title', '')
        prompt_template = params.get('prompt', '')
        provider = params.get('provider') or load('global').get('image_provider', 'yunwu')
        project_dir = params.get('project_dir', '')

        log.info('[生图] 开始 product_id=%s provider=%s', product_id, provider)
        try:
            # 1. 获取场景
            log.info('[生图] 获取场景: title=%s', title[:20])
            scene = generate_scene_prompt(main_image_path, title)
            log.info('[生图] 场景=%s', scene)

            # 2. 替换提示词 <> 占位符，加四宫格前缀
            prompt = re.sub(r'<[^>]*>', scene, prompt_template)
            prompt = f'四宫格，{prompt}'
            log.info('[生图] 最终提示词=%s', prompt[:60])

            # 3. 读取主图
            with open(main_image_path, 'rb') as f:
                image_b64 = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(main_image_path)[1].lower()
            mime_type = 'image/png' if ext == '.png' else 'image/jpeg'

            # 4. 生图
            output_dir = os.path.join(DATA_DIR, 'generated_images')
            generator = HotangImageGenerator() if provider == 'hotang' else YunwuImageGenerator()
            log.info('[生图] 调用生成器...')
            file_path = generator.generate(prompt=prompt, image_b64=image_b64, mime_type=mime_type, output_dir=output_dir)
            log.info('[生图] 生图完成: %s', file_path)

            # 5. 裁剪四宫格
            with open(file_path, 'rb') as f:
                gen_b64 = base64.b64encode(f.read()).decode()
            split_dir = os.path.join(project_dir, 'images', str(product_id), 'role_images') if project_dir else os.path.join(DATA_DIR, 'generated_images', str(product_id))
            previous_status = self._load_status(project_dir, product_id) if project_dir else {}
            if os.path.isdir(split_dir):
                shutil.rmtree(split_dir, ignore_errors=True)
            previous_video = previous_status.get('video', '')
            if previous_video and os.path.isfile(previous_video):
                os.remove(previous_video)
            parts = split_image_to_quadrants(gen_b64, 'image/jpeg', output_dir=split_dir)
            log.info('[生图] 裁剪完成，共 %d 张', len(parts))

            # 6. 写 status.json
            role_paths = [p['path'] for p in parts]
            self._update_status(project_dir, product_id, {'role_images': role_paths, 'video': ''})

            return {'ok': True, 'path': file_path, 'parts': parts}
        except Exception as e:
            log.error('[生图] 失败 product_id=%s: %s', product_id, e)
            return {'ok': False, 'message': str(e)}

    def batch_generate_image(self, params):
        items = params.get('items', [])
        g = load('global')
        provider = params.get('provider') or g.get('image_provider', 'yunwu')
        threads = int(g.get('image_threads', 2))

        def run_all():
            def run_one(item):
                self._update_status(item.get('project_dir', ''), item['product_id'], {'running': '生图中'})
                self.generate_image_task({**item, 'provider': provider})
                self._update_status(item.get('project_dir', ''), item['product_id'], {'running': ''})
            with ThreadPoolExecutor(max_workers=threads) as ex:
                list(ex.map(run_one, items))

        threading.Thread(target=run_all, daemon=True).start()
        return {'ok': True, 'async': True}

    def generate_video_task(self, params):
        from kling_video_generator import KlingVideoGenerator
        product_id = params.get('product_id', '')
        from urllib.parse import unquote
        role_image_path = unquote(params.get('role_image_path', ''))
        prompt = params.get('prompt', '')
        project_dir = params.get('project_dir', '')

        log.info('[生视频] 开始 product_id=%s', product_id)
        log.info('[生视频] role_image_path=%s', role_image_path)
        try:
            with open(role_image_path, 'rb') as f:
                image_b64 = base64.b64encode(f.read()).decode()

            output_dir = os.path.join(DATA_DIR, 'success_video')
            os.makedirs(output_dir, exist_ok=True)

            log.info('[生视频] 调用可灵生成器...')
            generator = KlingVideoGenerator()
            file_path = generator.generate(image_b64=image_b64, prompt=prompt, output_dir=output_dir)

            final_path = os.path.join(output_dir, f'{product_id}.mp4')
            if file_path != final_path:
                os.replace(file_path, final_path)
            log.info('[生视频] 完成: %s', final_path)

            self._update_status(project_dir, product_id, {'video': final_path})
            return {'ok': True, 'path': final_path}
        except Exception as e:
            log.error('[生视频] 失败 product_id=%s: %s', product_id, e)
            return {'ok': False, 'message': str(e)}

    def batch_generate_video(self, params):
        items = params.get('items', [])
        g = load('global')
        threads = int(g.get('video_threads', 1))

        def run_all():
            def run_one(item):
                self._update_status(item.get('project_dir', ''), item['product_id'], {'running': '生视频中'})
                self.generate_video_task(item)
                self._update_status(item.get('project_dir', ''), item['product_id'], {'running': ''})
            with ThreadPoolExecutor(max_workers=threads) as ex:
                list(ex.map(run_one, items))

        threading.Thread(target=run_all, daemon=True).start()
        return {'ok': True, 'async': True}

    def generate_kling_video(self, params):
        try:
            from kling_video_generator import KlingVideoGenerator
            generator = KlingVideoGenerator()
            file_path = generator.generate(
                image_b64=params.get('image_b64', ''),
                prompt=params.get('prompt', ''),
            )
            return {'ok': True, 'path': file_path}
        except Exception as e:
            log.error(f"可灵视频生成失败：{e}")
            return {'ok': False, 'message': str(e)}

    def kling_login(self):
        try:
            import subprocess
            import sys
            if is_frozen():
                subprocess.Popen([sys.executable, '--kling-login'])
            else:
                script = os.path.join(os.path.dirname(__file__), 'kling_login_runner.py')
                subprocess.Popen([sys.executable, script])
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'message': str(e)}

    def debug_scene_prompt(self, params):
        try:
            import tempfile, base64, os
            image_b64 = params.get('image_b64', '')
            title = params.get('title', '')
            img_bytes = base64.b64decode(image_b64)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(img_bytes)
                tmp_path = f.name
            try:
                scene = generate_scene_prompt(tmp_path, title)
            finally:
                os.unlink(tmp_path)
            return {'ok': True, 'scene': scene}
        except Exception as e:
            log.error(f"场景生成调试失败：{e}")
            return {'ok': False, 'message': str(e)}

    def split_image_four_grid(self, params):
        try:
            parts = split_image_to_quadrants(
                image_b64=params.get('image_b64', ''),
                mime_type=params.get('mime_type', ''),
                output_dir=params.get('output_dir'),
            )
            return {'ok': True, 'parts': parts}
        except Exception as e:
            log.error(f"图片切割失败：{e}")
            return {'ok': False, 'message': f'图片切割失败：{e}'}

    def get_log_stats(self):
        return get_log_stats()

    def clear_logs(self):
        try:
            clear_logs()
            log.info("日志已清理")
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'message': str(e)}

    def pack_logs(self):
        try:
            path = pack_logs(os.path.join(DATA_DIR, 'log'))
            log.info(f"日志已打包：{path}")
            return {'ok': True, 'path': path}
        except Exception as e:
            return {'ok': False, 'message': str(e)}

    def _load_status(self, project_dir: str, product_id: str) -> dict:
        status_path = os.path.join(project_dir, 'images', str(product_id), 'status.json')
        if not os.path.exists(status_path):
            return {}
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _update_status(self, project_dir: str, product_id: str, updates: dict):
        if not project_dir:
            return
        status_path = os.path.join(project_dir, 'images', str(product_id), 'status.json')
        os.makedirs(os.path.dirname(status_path), exist_ok=True)
        with STATUS_LOCK:
            status = {}
            if os.path.exists(status_path):
                try:
                    with open(status_path, 'r', encoding='utf-8') as f:
                        status = json.load(f)
                except Exception:
                    pass
            status.update(updates)
            tmp_path = f'{status_path}.{uuid.uuid4().hex}.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, status_path)
        log.info('[status] 已更新 product_id=%s: %s', product_id, list(updates.keys()))

    def _build_image_result(self, file_path):
        with open(file_path, 'rb') as handle:
            b64 = base64.b64encode(handle.read()).decode()
        ext = os.path.splitext(file_path)[1].lstrip('.') or 'png'
        return {'ok': True, 'path': file_path, 'b64': b64, 'ext': ext}


def main():
    html_path = resource_path('backend', 'vue', 'index.html')
    url = f'file://{html_path}'
    api = Api()
    webview.create_window('女装助手', url, width=1200, height=800, maximized=True, js_api=api)
    webview.start()


if __name__ == '__main__':
    import sys
    if '--kling-login' in sys.argv:
        from kling_login_runner import main as kling_login_main
        kling_login_main()
    else:
        main()
