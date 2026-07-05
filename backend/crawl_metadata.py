CRAWL_CATEGORIES = [
    {'value': '0', 'label': '全部'},
    {'value': '1', 'label': '母婴用品'},
    {'value': '2', 'label': '美妆个护'},
    {'value': '3', 'label': '图书&杂志&音频'},
    {'value': '5', 'label': '电脑办公'},
    {'value': '6', 'label': '时尚配件'},
    {'value': '7', 'label': '食品饮料'},
    {'value': '8', 'label': '家具'},
    {'value': '9', 'label': '保健'},
    {'value': '10', 'label': '收藏品'},
    {'value': '11', 'label': '家装建材'},
    {'value': '12', 'label': '居家日用'},
    {'value': '13', 'label': '家电'},
    {'value': '14', 'label': '珠宝与衍生品'},
    {'value': '15', 'label': '儿童时尚'},
    {'value': '16', 'label': '厨房用品'},
    {'value': '17', 'label': '箱包'},
    {'value': '18', 'label': '男装与男士内衣'},
    {'value': '19', 'label': '穆斯林时尚'},
    {'value': '20', 'label': '宠物用品'},
    {'value': '21', 'label': '手机与数码'},
    {'value': '22', 'label': '鞋靴'},
    {'value': '23', 'label': '运动与户外'},
    {'value': '24', 'label': '家纺布艺'},
    {'value': '25', 'label': '五金工具'},
    {'value': '26', 'label': '玩具和爱好'},
    {'value': '27', 'label': '汽车与摩托车'},
    {'value': '28', 'label': '女装与女士内衣'},
    {'value': '29', 'label': '虚拟商品'},
    {'value': '31', 'label': '二手'},
]

CRAWL_REGIONS = [
    {'value': 'US', 'label': '美国'},
    {'value': 'ID', 'label': '印度尼西亚'},
    {'value': 'TH', 'label': '泰国'},
    {'value': 'MY', 'label': '马来西亚'},
    {'value': 'VN', 'label': '越南'},
    {'value': 'GB', 'label': '英国'},
    {'value': 'PH', 'label': '菲律宾'},
    {'value': 'SG', 'label': '新加坡'},
    {'value': 'ES', 'label': '西班牙'},
    {'value': 'MX', 'label': '墨西哥'},
    {'value': 'IT', 'label': '意大利'},
    {'value': 'JP', 'label': '日本'},
    {'value': 'BR', 'label': '巴西'},
    {'value': 'DE', 'label': '德国'},
    {'value': 'FR', 'label': '法国'},
]

SELLER_TYPE_OPTIONS = [
    {'value': 'over_sea', 'label': '跨境店'},
    {'value': 'local', 'label': '本土店'},
    {'value': 'full_managed', 'label': '全托管店'},
]

RANK_TYPE_OPTIONS = [
    {'value': 1, 'label': '日榜'},
    {'value': 2, 'label': '周榜'},
    {'value': 3, 'label': '月榜'},
]

DEFAULT_CRAWL_SETTINGS = {
    'region': 'US',
    'categoryId': '28',
    'count': 48,
    'sellerTypes': ['full_managed'],
    'rankType': 1,
}


def get_category_name(category_id: str) -> str | None:
    category_id = str(category_id)
    for item in CRAWL_CATEGORIES:
        if item['value'] == category_id:
            return item['label']
    return None


def get_crawl_metadata() -> dict:
    return {
        'regions': CRAWL_REGIONS,
        'categories': CRAWL_CATEGORIES,
        'seller_types': SELLER_TYPE_OPTIONS,
        'rank_types': RANK_TYPE_OPTIONS,
        'defaults': DEFAULT_CRAWL_SETTINGS,
    }
