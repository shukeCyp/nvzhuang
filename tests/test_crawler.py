import json
import logging
import os
import sys
import unittest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from crawler import fetch_ranking_page


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {'ok': True}


class FakeSession:
    def __init__(self):
        self.url = None
        self.headers = None
        self.timeout = None

    def get(self, url, headers=None, timeout=None):
        self.url = url
        self.headers = headers
        self.timeout = timeout
        return FakeResponse()


class CrawlerTests(unittest.TestCase):
    def test_fetch_ranking_page_logs_request_url(self):
        session = FakeSession()

        with self.assertLogs('crawler', level=logging.INFO) as logs:
            fetch_ranking_page(session, 'cookie=value', 'US', '28', 2, '20260704')

        message = '\n'.join(logs.output)
        self.assertIn('https://www.tabcut.com/api/trpc/ranking.goods.rankingData?input=', message)
        self.assertIn('"pageNo":2', message)
        self.assertIn('"region":"US"', message)
        self.assertIn('"categoryId":"28"', message)
        self.assertEqual(json.loads(session.url.split('input=', 1)[1])['bizDate'], '20260704')

    def test_fetch_ranking_page_uses_selected_seller_types(self):
        session = FakeSession()

        fetch_ranking_page(
            session,
            'cookie=value',
            'US',
            '28',
            1,
            '20260704',
            seller_type='over_sea,local,full_managed',
        )

        input_param = json.loads(session.url.split('input=', 1)[1])
        self.assertEqual(input_param['sellerType'], 'over_sea,local,full_managed')

    def test_fetch_ranking_page_uses_selected_rank_type_and_biz_date(self):
        session = FakeSession()

        fetch_ranking_page(
            session,
            'cookie=value',
            'US',
            '28',
            1,
            '20260628',
            seller_type='full_managed',
            rank_type=2,
        )

        input_param = json.loads(session.url.split('input=', 1)[1])
        self.assertEqual(input_param['rankType'], 2)
        self.assertEqual(input_param['bizDate'], '20260628')


if __name__ == '__main__':
    unittest.main()
