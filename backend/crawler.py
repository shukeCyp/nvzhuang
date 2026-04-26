import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests
from crawl_metadata import get_category_name

log = logging.getLogger(__name__)

PAGE_SIZE = 24
MAX_IMAGE_COUNT = 10
MAX_DOWNLOAD_WORKERS = 20


def get_biz_date() -> str:
    now = datetime.now()
    delta = 2 if now.hour < 12 else 1
    return (now - timedelta(days=delta)).strftime('%Y%m%d')


def sanitize_filename(value: str) -> str:
    if not value:
        return value
    for char in '/\\:*?"<>|':
        value = value.replace(char, '-')
    return value.strip()


def clean_image_url(image_url: str) -> str:
    if not image_url:
        return image_url
    return image_url.replace('resize,w_246,h_246/', '')


def create_download_directory(data_dir: str, region: str, category_name: str) -> str:
    folder_name = f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-{sanitize_filename(category_name)}-{region}"
    download_path = os.path.join(data_dir, folder_name)
    os.makedirs(os.path.join(download_path, 'images'), exist_ok=True)
    os.makedirs(os.path.join(download_path, 'items'), exist_ok=True)
    return download_path


def fetch_ranking_page(session: requests.Session, cookie: str, region: str, category_id: str, page_no: int, biz_date: str) -> dict:
    input_param = (
        f'{{"pageNo":{page_no},"pageSize":{PAGE_SIZE},"rankType":1,'
        f'"bizDate":"{biz_date}","region":"{region}","categoryId":"{category_id}",'
        f'"orderType":"1","sellerType":"full_managed"}}'
    )
    url = f'https://www.tabcut.com/api/trpc/ranking.goods.rankingData?input={input_param}'
    headers = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://www.tabcut.com/',
    }
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_products(payload: dict) -> tuple[list[dict], dict]:
    if not isinstance(payload, dict):
        return [], {}

    candidates = [
        payload.get('result', {}).get('data', {}).get('result'),
        payload.get('result', {}).get('data', {}).get('json'),
        payload.get('result', {}).get('data'),
        payload.get('data'),
    ]

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        data = candidate.get('data')
        if isinstance(data, list):
            return data, candidate

    return [], {}


def parse_item(item: dict) -> dict:
    price_list = item.get('priceList') or []
    return {
        'product_id': item.get('itemId'),
        'title': item.get('itemName'),
        'price': price_list[0].get('local') if price_list else None,
        'original_price': None,
        'discount_rate': None,
        'sales_count': (item.get('soldCountInfo') or {}).get('periodCurrent'),
        'rating': None,
        'review_count': None,
        'image_url': clean_image_url(item.get('itemPicUrl')),
        'seller_name': item.get('sellerName'),
        'category': item.get('categoryName'),
        'rank': item.get('rank'),
        'gmv': ((item.get('gmvInfo') or {}).get('periodCurrent') or {}).get('local'),
        'total_sales': (item.get('soldCountInfo') or {}).get('total'),
        'commission_rate': item.get('commissionRate'),
        'seller_type': item.get('sellerType'),
        'growth_rate': item.get('soldCountGrowthRate'),
        'creator_count': ((item.get('relatedCreatorInfo') or {}).get('period90d')),
        'video_count': ((item.get('relatedVideoInfo') or {}).get('period90d')),
        'live_count': ((item.get('relatedLiveInfo') or {}).get('period90d')),
        'raw_data': item,
    }


def save_item_json(item_data: dict, save_dir: str) -> bool:
    product_id = item_data.get('product_id')
    if not product_id:
        return False

    items_dir = os.path.join(save_dir, 'items')
    os.makedirs(items_dir, exist_ok=True)
    filepath = os.path.join(items_dir, f'{product_id}.json')
    with open(filepath, 'w', encoding='utf-8') as handle:
        json.dump(item_data, handle, ensure_ascii=False, indent=2)
    return True


def download_product_images(base_url: str, product_id: str, save_dir: str, max_images: int = MAX_IMAGE_COUNT) -> int:
    if not base_url or not product_id:
        return 0

    product_image_dir = os.path.join(save_dir, 'images', str(product_id))
    os.makedirs(product_image_dir, exist_ok=True)

    base_without_query, _, query = base_url.partition('?')
    url_base = base_without_query.rsplit('0.webp', 1)[0] if '0.webp' in base_without_query else base_without_query.rsplit('.webp', 1)[0]
    query_suffix = f'?{query}' if query else ''

    success_count = 0
    for index in range(max_images):
        image_url = f'{url_base}{index}.webp{query_suffix}'
        filepath = os.path.join(product_image_dir, f'{index + 1}.webp')

        if os.path.exists(filepath):
            success_count += 1
            continue

        try:
            response = requests.get(
                image_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                },
                timeout=30,
            )
            if response.status_code == 404:
                break
            response.raise_for_status()
            with open(filepath, 'wb') as handle:
                handle.write(response.content)
            success_count += 1
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                break
            log.warning('商品 %s 的第 %s 张图片下载失败：%s', product_id, index + 1, exc)
            break
        except Exception as exc:
            log.warning('商品 %s 的第 %s 张图片下载异常：%s', product_id, index + 1, exc)
            continue

    return success_count


def crawl(
    cookie: str,
    region: str,
    category_id: str,
    count: int,
    data_dir: str,
    category_name: str | None = None,
    progress_callback=None,
) -> dict:
    if not cookie:
        raise ValueError('未提供 Tabcut Cookie')

    biz_date = get_biz_date()
    requested_pages = (count + PAGE_SIZE - 1) // PAGE_SIZE
    all_raw_items: list[dict] = []
    detected_category_name = category_name or get_category_name(category_id) or category_id
    total_available = None

    log.info('开始请求 Tabcut 排名数据，业务日期=%s，地区=%s，分类ID=%s，抓取数量=%s，预计页数=%s', biz_date, region, category_id, count, requested_pages)
    if progress_callback:
        progress_callback(5, '开始请求排名数据')

    with requests.Session() as session:
        for page_no in range(1, requested_pages + 1):
            payload = fetch_ranking_page(session, cookie, region, category_id, page_no, biz_date)
            page_items, page_meta = extract_products(payload)
            log.info('第 %s 页解析完成，本页商品数=%s', page_no, len(page_items))
            if progress_callback:
                page_progress = min(45, 5 + int(page_no / max(requested_pages, 1) * 40))
                progress_callback(page_progress, f'第 {page_no} 页抓取完成，本页 {len(page_items)} 条')

            if not page_items:
                log.warning('第 %s 页未解析到商品数据', page_no)
                break

            if not category_name:
                detected_category_name = page_items[0].get('categoryName') or detected_category_name

            total_available = page_meta.get('total') if isinstance(page_meta, dict) else total_available
            all_raw_items.extend(page_items)
            log.info('当前累计商品数=%s', len(all_raw_items))

            if len(all_raw_items) >= count:
                log.info('已达到目标抓取数量，停止继续翻页')
                break
            if total_available is not None and len(all_raw_items) >= total_available:
                log.info('已达到接口可返回的全部商品数量，停止继续翻页')
                break

        items = [parse_item(item) for item in all_raw_items[:count]]
        download_dir = create_download_directory(data_dir, region, detected_category_name)
        log.info('已创建保存目录：%s', download_dir)
        if progress_callback:
            progress_callback(55, f'已创建保存目录，准备保存 {len(items)} 条商品数据')

        for item in items:
            save_item_json(item, download_dir)
        log.info('商品 JSON 保存完成，共 %s 条', len(items))
        if progress_callback:
            progress_callback(65, f'商品 JSON 保存完成，共 {len(items)} 条')

        lock = threading.Lock()
        image_stats = {'products': 0, 'images': 0, 'failed': 0}
        completed_images = {'count': 0}

        def process_images(item: dict) -> None:
            image_url = item.get('image_url')
            product_id = item.get('product_id')
            downloaded = download_product_images(image_url, product_id, download_dir)
            with lock:
                completed_images['count'] += 1
                if downloaded > 0:
                    image_stats['products'] += 1
                    image_stats['images'] += downloaded
                else:
                    image_stats['failed'] += 1
                if progress_callback and items:
                    image_progress = 65 + int(completed_images['count'] / len(items) * 30)
                    progress_callback(
                        min(95, image_progress),
                        f'图片下载进度 {completed_images["count"]}/{len(items)}',
                    )
                log.info(
                    '第 %s/%s 个商品图片下载完成，商品ID=%s，成功下载 %s 张',
                    completed_images['count'],
                    len(items),
                    product_id,
                    downloaded,
                )

        with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as pool:
            futures = [pool.submit(process_images, item) for item in items]
            for future in as_completed(futures):
                future.result()

    summary = {
        'total_count': len(items),
        'region': region,
        'category_id': category_id,
        'category_name': detected_category_name,
        'crawl_date': datetime.now().isoformat(),
        'biz_date': biz_date,
        'download_path': download_dir,
        'save_dir': download_dir,
        'image_product_count': image_stats['products'],
        'image_count': image_stats['images'],
        'image_failed_count': image_stats['failed'],
        'requested_count': count,
        'available_count': total_available,
    }

    with open(os.path.join(download_dir, 'summary.json'), 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    log.info(
        '抓取完成，商品数=%s，成功下载图片数=%s，图片下载失败商品数=%s，保存目录=%s',
        summary['total_count'],
        summary['image_count'],
        summary['image_failed_count'],
        download_dir,
    )
    if progress_callback:
        progress_callback(100, '抓取完成')
    return summary
