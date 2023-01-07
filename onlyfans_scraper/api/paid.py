r"""
               _          __
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|
                  |___/                                                        |_|
"""
from ..constants import purchased_contentEP
from ..utils import auth, config
import httpx
import re


def scrape_paid():
    """Takes headers to access onlyfans as an argument and then checks the purchased content
    url to look for any purchased content. If it finds some it will return it as a list."""
    media_to_download = []
    offset = 0
    hasMore = True
    headers = auth.make_headers(auth.read_auth())
    with httpx.Client(http2=True, headers=headers) as c:
        while hasMore:
            headers = auth.make_headers(auth.read_auth())
            auth.add_cookies(c)
            url = purchased_contentEP.format(offset)
            offset += 10
            c.headers.update(auth.create_sign(url, headers))
            r = c.get(url, timeout=None)
            if not r.is_error:
                if "hasMore" in r.json():
                    hasMore = r.json()['hasMore']
                for item in r.json()['list']:
                    for i in item['media']:
                        if "src" in i:
                            src = i['src']
                        if "source" in i:
                            source = i['source']
                        if source:
                            media_to_download.append(source['source'])
                        else:
                            media_to_download.append(src['src'])
    return media_to_download


def download_paid(media):
    """Takes a list of purchased content and downloads it."""
    save_location = config.get('save_location') + "Paid Content"
    headers = auth.make_headers(auth.read_auth())
    with httpx.AsyncClient( http2=True, headers=headers) as client:
        auth.add_cookies(client)
        for item in media:
            r = client.get(item)
            d = r.headers['content-disposition']
            fname = re.findall("filename=", d)[0]
            print(fname)



