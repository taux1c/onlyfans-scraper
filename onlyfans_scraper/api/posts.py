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
    archivedEP, archivedNextEP,
    paidEP, paidNextEP
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

def scrape_paid_posts(headers, offset=0) -> list:
    ep = paidNextEP if offset else paidEP
    url = ep.format(offset)

    with httpx.Client(http2=True, headers=headers) as c:
        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))

        r = c.get(url, timeout=None)
        if not r.is_error:
            posts = r.json.get('list', [])
            if not posts:
                return posts
            posts += scrape_paid_posts(headers, offset + len(posts))
            return posts
        r.raise_for_status()


def scrape_timeline_posts(headers, model_id, timestamp=0) -> list:
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


def parse_posts(posts: list) -> list[tuple[str, str, int, str]]:
    urls = []
    for post in posts:
        if 'media' not in post:
            continue
        for media in post.get('media', []):
            for item in media:
                match item:
                    # posts
                    case {"info": {"source":{"source": source}}, "createdAt": createdAt, "id": itemId, "type": itemtype, "canView": True }:
                        urls.append((source, createdAt, itemId, itemtype))
                    # paid posts
                    case {"source": {"source": source}, "id": itemId, "type": itemtype}:
                        urls.append((source, post.get('createdAt',None), itemId, itemtype))
    return urls
            
            

    # # media = [post['media'] for post in posts if post.get('media')]
    # urls = [
    #     (i["source"]["source"], i['createdAt'], i['id'], i['type']) 
    #     for m in media 
    #     for i in m 
    #     if i['canView']
    # ]
    # return urls
