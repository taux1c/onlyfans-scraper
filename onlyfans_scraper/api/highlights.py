r"""
               _          __                                                                      
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __ 
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |   
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|   
                  |___/                                                        |_|                
"""

import asyncio
from itertools import chain

import httpx

from ..constants import highlightsWithStoriesEP, highlightsWithAStoryEP, storyEP
from ..utils import auth


def scrape_highlights(headers, user_id) -> list:
    with httpx.Client(http2=True, headers=headers) as c:
        url_stories = highlightsWithStoriesEP.format(user_id)
        url_story = highlightsWithAStoryEP.format(user_id)

        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url_stories, headers))
        r_multiple = c.get(url_stories, timeout=None)

        c.headers.update(auth.create_sign(url_story, headers))
        r_one = c.get(url_story, timeout=None)

        if not r_multiple.is_error and not r_one.is_error:
            return r_multiple.json(), r_one.json()

        r_multiple.raise_for_status()
        r_one.raise_for_status()


def parse_highlights(highlights: list) -> list:
    if not highlights['hasMore']:
        return []

    highlight_ids = [highlight['id'] for highlight in highlights.get("data")]
    return highlight_ids


async def process_highlights_ids(headers, ids: list) -> list:
    if not ids:
        return []

    tasks = [scrape_story(headers, id_) for id_ in ids]
    results = await asyncio.gather(*tasks)
    return list(chain.from_iterable(results))


async def scrape_story(headers, story_id: int) -> list:
    async with httpx.AsyncClient(http2=True, headers=headers) as c:
        url = storyEP.format(story_id)

        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))

        r = await c.get(url, timeout=None)
        if not r.is_error:
            return r.json()['stories']
        r.raise_for_status()


def parse_stories(stories: list):
    media = [story['media'] for story in stories]
    urls = [(i['files']['source']['url'], i['createdAt'], i['id'], i['type'])
            for m in media for i in m if i['canView']]
    return urls
