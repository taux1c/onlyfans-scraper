
from onlyfans_scraper.constants import lists_EP
import pandas
import requests
from onlyfans_scraper.utils import auth
import asyncio
hasMore_name = ""
list_name = ""
offset = 0
hasMore = True
all_lists = []
async def get_list(**kwargs):
    with requests.session() as s:
        while hasMore:
            url = lists_EP.format(offset)
            headers = auth.make_headers(auth.read_auth())
            headers = auth.create_sign(url,headers)
            s.headers.update(headers)
            with s.get(url) as r:
                jdata = r.json()
                print(jdata)
                # for item in jdata:
                #     if type(r.json()[item]) == bool:
                #         hasMore_name = item
                #         hasMore = r.json()[item]
                #     elif type(r.json()[item]) == list:
                #         list_name = item
                #     else:
                #         print("New items detected. Item {} of type {}".format(item, type(r.json()[item])))
                # if list_name in r.json():
                #     print(r.json()[list_name])
                # offset += 10