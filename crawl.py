#! /usr/bin/env python
# coding: utf-8

import requests
import time

headers = {
    'Host': 'm.weibo.cn',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://m.weibo.cn/u/5175429989'
}


def get_page(page):
    '''请求url，并获取内容
    :param page:
    :return:
    '''
    params = {
        'type': 'uid',
        'value': '5175429989',
        'containerid': '1076035175429989',
        'page': page

    }
    url = 'https://m.weibo.cn/api/container/getIndex'
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            return res.json()
    except requests.ConnectionError as e:
        print('Error', e.args)


def parse_page(json, page):
    if json:
        items = json.get('data').get('cards')
        for index, item in enumerate(items):
            if page == 1 and index == 1:
                continue
            else:
                item = item.get('mblog')
                weibo = {}
                weibo['id'] = item.get('id')
                # weibo['text'] = pq(item.get('text')).text()
                weibo['attitudes'] = item.get('attitudes_count')
                weibo['comments'] = item.get('comments_count')
                weibo['reposts'] = item.get('reposts_count')
                yield weibo


def get_comments(wb_id):
    Data = []
    url = 'https://m.weibo.cn/api/comments/show?id={id}'.format(id=wb_id)
    page_url = 'https://m.weibo.cn/api/comments/show?id={id}&page={page}'
    Resp = requests.get(url, headers=headers)
    page_max_num = Resp.json()['data']['max']
    for i in range(page_max_num):
        p_url = page_url.format(id=wb_id, page=i + 1)
        resp = requests.get(p_url, headers=headers)
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
            print(d)
            time.sleep(1)


if __name__ == '__main__':
    for page in range(1, 11):
        json = get_page(page)
        results = parse_page(json, page)
        for result in results:
            print(result)
            #
            time.sleep(1)
    get_comments('4417893804039537')
