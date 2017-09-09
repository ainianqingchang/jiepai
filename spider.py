import requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json
import pymongo
from config import *
import os
import re
from hashlib import md5
from multiprocessing import Pool
client=pymongo.MongoClient(MONGO_URL,connect=False)
db=client[MONGO_DB]

def get_page_index(offset,keyword):
    data={
        'offset':offset,
        'format':'json',
        'keyword':keyword,
        'autoload':'true',
        'count':'20',
        'cur_tab':1
    }
    url='https://www.toutiao.com/search_content/?'
    try:
        response=requests.get(url,params=data)
        if response.status_code==200:
            return response.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None

def parse_images(image_detail):
    images=[]
    for item in image_detail:
        url=item.get('url')
        pattern=re.compile(r'(?<=)/large/(?=)')
        url=pattern.sub('/origin/',url)
        images.append(url)
    return images



def parse_page_index(html):
    data=json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            if item and 'article_url' in item.keys():
                url = item.get('article_url')
                title=item.get('title')
                image_detail=item.get('image_detail')
                images=parse_images(image_detail)
                for image in images:
                    download_image(image)
                dic={
                    'url':url,
                    'title':title,
                    'images':images
                }
                yield dic

def download_image(url):
    print("在下载..",url)
    try:
        response=requests.get(url)
        if response.status_code==200:
            save_image(response.content)
        return None
    except RequestException:
        print('请求出错')
        return None

def save_image(content):
    file_path='{0}/{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存贮到mogodb成功',result)
        return True
    return False

def main(offset):
    html=get_page_index(offset,KEYWORD)
    for dic in parse_page_index(html):
         save_to_mongo(dic)



if __name__ == "__main__":
    group=[ x*20 for x in range(GROUP_START,GROUP_END)]
    pool=Pool()
    pool.map(main,group)