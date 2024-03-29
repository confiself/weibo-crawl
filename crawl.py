#! /usr/bin/env python
# coding: utf-8

import requests
import time
import os
import json


class CrawlComments(object):
    """
    需要不断更换cookie
    参考微博爬虫，自己实现
    """
    headers = {
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://m.weibo.cn/u/5175429989',
        'Cookie': '_T_WM=76414085534; SUB=_2A25wiPo7DeRhGedI6VUX8ifJyj-IHXVQcoZzrDV6PUJbktAKLWekkW1NV74_lxJ-Qtw5-OEZgWgsddE9ho-xPG6O; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5wUH6RDWfxkGin5-qfbUWT5JpX5KzhUgL.Fo2ceoMceo.feKe2dJLoIEBLxKqL12-LBKMLxKBLBonL1KqLxKqLBo-LB--LxKqLBozL1h.t; SUHB=0D-0bw_siFdpnC; SSOLoginState=1569491563; MLOGIN=1; XSRF-TOKEN=1d872b; WEIBOCN_FROM=1110006030; M_WEIBOCN_PARAMS=lfid%3D100803%26luicode%3D20000174%26uicode%3D20000174'
    }

    def __init__(self, uid, container_id):
        self.uid = uid
        self.container_id = container_id
        self.comments_finished = set()
        self.comments_finished_file = '/opt/app/data/wei_bo_finished_info.txt'
        self.comments_file = '/opt/app/data/wei_bo_comments.txt'
        self.sess = requests.session()
        self.sess.headers = self.headers
        self._load()

    def _load(self):
        if not os.path.exists(self.comments_finished_file):
            return
        with open(self.comments_finished_file) as f:
            self.comments_finished = set(map(lambda x: x.strip(), f.readlines()))

    def _add_page(self, page_key):
        self.comments_finished.add(page_key)
        with open(self.comments_finished_file, 'a') as f_finished:
            f_finished.writelines(page_key + '\n')

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
            self._add_page(page_key)
            for content in contents:
                comments = self.get_comments(content['id'])
                self.save_comments(comments)
            time.sleep(1)

    def save_comments(self, comments):
        with open(self.comments_finished_file, 'a') as f_finished, \
                open(self.comments_file, 'a') as f_comments:
            for comment in comments:
                comment_key = 'comment_id,{}'.format(comment['id'])
                if comment_key in self.comments_finished:
                    continue
                self.comments_finished.add(comment_key)
                f_finished.writelines(comment_key + '\n')
                comment = json.dumps(comment, ensure_ascii=False)
                f_comments.writelines(comment + '\n')
                print('{} finished, add comment {}'.format(len(self.comments_finished), comment))

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
            res = self.sess.get(url, headers=self.headers, params=params)
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
        resp = self.sess.get(url, headers=self.headers)
        if 'data' not in resp.json()['data']:
            return []
        page_max_num = resp.json()['data']['max']
        comments = []
        for i in range(page_max_num):
            p_url = page_url.format(id=wb_id, page=i + 1)
            resp = self.sess.get(p_url, headers=self.headers)
            if 'data' not in resp.json():
                print(resp.json())
                continue
            resp_data = resp.json()['data']
            data = resp_data['data']
            for d in data:
                if 'reply_id' not in d:
                    continue
                _comment = {'id': d['id'],
                            'reply_id': d['reply_id'],
                            'text': d['text'],
                            'reply_text': d['reply_text'],
                            'user_name': d['user']['screen_name']
                            }
                comments.append(_comment)

        return comments

if __name__ == '__main__':
    _comments = CrawlComments('5175429989', '1076035175429989')
    _comments.crawl()
