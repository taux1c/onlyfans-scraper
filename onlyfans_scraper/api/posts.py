r"""
               _          __                                                                      
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __ 
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |   
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|   
                  |___/                                                        |_|                
"""

import httpx


from ..constants import (
    timelineEP, timelineNextEP,
    timelinePinnedEP,
    archivedEP, archivedNextEP, of_posts_list_name
)
from ..utils import auth


def scrape_pinned_posts(headers, model_id) -> list:
    with httpx.Client(http2=True, headers=headers) as c:
        url = timelinePinnedEP.format(model_id)

        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))

        r = c.get(url, timeout=None)
        if not r.is_error:
            return r.json()['list']
        r.raise_for_status()


def scrape_timeline_posts2(headers, model_id, timestamp=0) -> list:
    ep = timelineNextEP if timestamp else timelineEP
    url = ep.format(model_id, timestamp)

    with httpx.Client(http2=True, headers=headers) as c:
        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))

        r = c.get(url, timeout=None)
        if not r.is_error:
            posts = r.json()['list']
            if not posts:
                return posts
            posts += scrape_timeline_posts(
                headers, model_id, posts[-1]['postedAtPrecise'])
            return posts
        r.raise_for_status()


# REWRITE OF THE ABOVE FUNCTION WITH A SECOND SECTION TO HANDLE ADDITIONAL REQUESTS WITHOUT RECURSION AND FIGURE OUT LIST NAME AUTOMATICALLY.
def scrape_timeline_posts(headers, model_id, max_timestamp=0):
    ep = timelineNextEP if timestamp else timelineEP
    url = ep.format(model_id, timestamp)
    with httpx.Client(http2=True, headers=headers) as c:
        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))
        r = c.get(url, timeout=None)
        if not r.is_error:
            for x in r.json():
                if isinstance(r.json()[x],list):
                    the_list = r.json()[x]
        if 'hasMore' in r.json():
            has_more = r.json()['hasMore']
        else:
            print("Onlyfans has changed something! Sound the alarm!")
            return
        posts = r.json()[the_list]
        if not posts:
            return posts
        while has_more:
            posts += scrape_timeline_posts(
                headers, model_id, posts[-1]['postedAtPrecise'])
            return posts
        r.raise_for_status()


def scrape_archived_posts(headers, model_id, timestamp=0) -> list:
    ep = archivedNextEP if timestamp else archivedEP
    url = ep.format(model_id, timestamp)

    with httpx.Client(http2=True, headers=headers) as c:
        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))

        r = c.get(url, timeout=None)
        if not r.is_error:
            posts = r.json()['list']
            if not posts:
                return posts
            posts += scrape_archived_posts(
                headers, model_id, posts[-1]['postedAtPrecise'])
            return posts
        r.raise_for_status()


def parse_posts(posts: list):
    media = [post['media'] for post in posts if post.get('media')]
    urls = [
        (i['info']['source']['source'], i['createdAt'], i['id'], i['type']) for m in media for i in m if i['canView']]
    return urls
