#! /usr/bin/env python
# coding: utf-8

import requests
import time
import os


class CrawlComments(object):

    headers = {
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://m.weibo.cn/u/5175429989'
    }

    def __init__(self, uid, container_id):
        self.uid = uid
        self.container_id = container_id
        self.comments_finished = set()
        self.comments_file = '/opt/app/data/wei_bo_comments.txt'
        self._load()

    def _load(self):
        if not os.path.exists(self.comments_file):
            return
        with open(self.comments_file) as f:
            self.comments_finished = set(map(lambda x: x.strip(), f.readlines()))

    def crawl(self):
        page = 1
        while page != -1:
            page_key = 'page,{}'.format(page)
            if page_key in self.comments_finished:
                page += 1
                continue
            contents, page = self.get_page(page)
            if not contents:
                continue
            self.comments_finished.add(page_key)
            for content in contents:
                comments = self.get_comments(content['id'])
                self.save_comments(comments)
            time.sleep(1)

    def save_comments(self, comments):
        with open(self.comments_file, 'a') as f:
            for text, comment_id in comments:
                comment_key = 'comment_id,{}'
                if comment_key in self.comments_finished:
                    continue
                self.comments_finished.add(comment_key)
                f.writelines(text + '\n')

    def get_page(self, page):
        '''请求url，并获取内容
        :param page:
        :return:
        '''
        params = {
            'type': 'uid',
            'value': self.uid,
            'containerid': self.container_id,
            'page': page

        }
        url = 'https://m.weibo.cn/api/container/getIndex'
        try:
            res = requests.get(url, headers=self.headers, params=params)
            if res.status_code == 200 and 'data' in res.json():
                # finish detected
                if 'cards' not in res.json()['data'] or not res.json()['data']['cards']:
                    return None, -1
                cards = res.json()['data']['cards']
                return self.parse_page(cards, page), page + 1
        except requests.ConnectionError as e:
            print('Error', e.args)
        return None, page + 1

    @staticmethod
    def parse_page(cards, page):
        for index, item in enumerate(cards):
            if 'mblog' not in item:
                continue
            if page == 1 and index == 1:
                continue
            else:
                item = item.get('mblog')
                weibo = {'id': item.get('id'),
                         'attitudes': item.get('attitudes_count'),
                         'comments': item.get('comments_count'),
                         'reposts': item.get('reposts_count')}
                # weibo['text'] = pq(item.get('text')).text()
                yield weibo

    def get_comments(self, wb_id):
        url = 'https://m.weibo.cn/api/comments/show?id={id}'.format(id=wb_id)
        page_url = 'https://m.weibo.cn/api/comments/show?id={id}&page={page}'
        Resp = requests.get(url, headers=self.headers)
        page_max_num = Resp.json()['data']['max']
        for i in range(page_max_num):
            p_url = page_url.format(id=wb_id, page=i + 1)
            resp = requests.get(p_url, headers=self.headers)
            resp_data = resp.json()['data']
            data = resp_data['data']
            for d in data:
                review_id = d['id']
                like_counts = d['like_counts']
                source = d['source']
                username = d['user']['screen_name']
                image = d['user']['profile_image_url']
                verified = d['user']['verified']
                verified_type = d['user']['verified_type']
                profile_url = d['user']['profile_url']
                comment = d['text']
                yield comment
            time.sleep(1)


if __name__ == '__main__':
    _comments = CrawlComments('5175429989', '1076035175429989')
    _comments.crawl()
