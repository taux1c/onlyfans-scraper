r"""
               _          __                                                                      
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __ 
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |   
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|   
                  |___/                                                        |_|                
"""

import random
import time

import httpx
from revolution import Revolution

from ..api import posts
from ..constants import favoriteEP, postURL
from ..utils import auth


def get_posts(headers, model_id):
    with Revolution(desc='Getting posts...') as _:
        pinned_posts = posts.scrape_pinned_posts(headers, model_id)
        timeline_posts = posts.scrape_timeline_posts(headers, model_id)
        archived_posts = posts.scrape_archived_posts(headers, model_id)

    return pinned_posts + timeline_posts + archived_posts


def filter_for_unfavorited(posts: list) -> list:
    unfavorited_posts = [post for post in posts if not post['isFavorite']]
    return unfavorited_posts


def filter_for_favorited(posts: list) -> list:
    favorited_posts = [post for post in posts if post['isFavorite']]
    return favorited_posts


def get_post_ids(posts: list) -> list:
    ids = [post['id'] for post in posts if post['isOpened']]
    return ids


def like(headers, model_id, username, ids: list):
    with Revolution(desc='Liking posts...', total=len(ids)) as rev:
        for i in ids:
            with httpx.Client(http2=True, headers=headers) as c:
                url = favoriteEP.format(i, model_id)

                auth.add_cookies(c)
                c.headers.update(auth.create_sign(url, headers))

                r = c.post(url)
                if not r.is_error:
                    rev.update()
                else:
                    print(
                        f'{r.status_code} STATUS CODE: unable to like post at {postURL.format(i, username)}')
                time.sleep(random.uniform(0.8, 0.9))


def unlike(headers, model_id, username, ids: list):
    with Revolution(desc='Unliking posts...', total=len(ids)) as rev:
        for i in ids:
            with httpx.Client(http2=True, headers=headers) as c:
                url = favoriteEP.format(i, model_id)

                auth.add_cookies(c)
                c.headers.update(auth.create_sign(url, headers))

                r = c.post(url)
                if not r.is_error:
                    rev.update()
                else:
                    print(
                        f'{r.status_code} STATUS CODE: unable to unlike post at {postURL.format(i, username)}')
                time.sleep(random.uniform(0.8, 0.9))
