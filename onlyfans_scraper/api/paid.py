r"""
               _          __
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|
                  |___/                                                        |_|
"""
from urllib.request import urlopen

from ..constants import purchased_contentEP
from ..utils import auth
import httpx
import pathlib
from ..utils.config import read_config
from hashlib import md5
import sqlite3 as sql
config = read_config()['config']
paid_content_list_name = 'list'

save_location = pathlib.Path(config.get('save_location'), 'Paid Content')
save_location.mkdir(parents=True,exist_ok=True)
#  SQL SETUP

db = sql.connect(pathlib.Path(save_location, 'paid.db'))
cursor = db.cursor()

create_table_command = "CREATE TABLE IF NOT EXISTS hashes(id integer PRIMARY KEY, hash text, file_name text)"



def add_to_db(hash,file_name):
    """Returns True if hash was not in the database and file can continue."""
    cursor.execute(create_table_command)
    db.commit()
    cursor.execute(f"SELECT * FROM hashes WHERE hash='{hash.hexdigest()}'")
    results = cursor.fetchall()
    if len(results) > 0:
        print("Working in the background. Simmer down.")
        return False
    cursor.execute("""INSERT INTO hashes(hash,file_name) VALUES(?,?)""",(hash.hexdigest(),file_name))
    db.commit()
    return True








def scrape_paid():
    """Takes headers to access onlyfans as an argument and then checks the purchased content
    url to look for any purchased content. If it finds some it will return it as a list."""
    media_to_download = []
    offset = 0
    hasMore = True
    headers = auth.make_headers(auth.read_auth())
    with httpx.Client(http2=True, headers=headers, follow_redirects=True) as c:
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
                # THIS NEEDS TO BE REWORKED TO WORK LIKE HIGHLIGHTS AND FIGURE OUT THE LIST NAME HAVEN'T HAD TIME.
                for item in r.json()[paid_content_list_name]:
                    for i in item['media']:
                        if "source" in i:
                            media_to_download.append(i['source']['source'])
                            print("Scraping, it isn't frozen. It takes time.")
    return media_to_download


def download_paid(media):
    """Takes a list of purchased content and downloads it."""
    headers = auth.make_headers(auth.read_auth())
    with httpx.Client(http2=True, headers=headers, follow_redirects=True) as c:
        auth.add_cookies(c)
        for item in media:
            r = c.get(item)
            rheaders = r.headers
            last_modified = rheaders.get("last-modified")
            file_name = item.split('.')[-2].split('/')[-1].strip("/,.;!_-@#$%^&*()+\\ ")
            content_type = rheaders.get("content-type").split('/')[-1]
            pathlib.Path.mkdir(pathlib.Path(save_location),parents=True,exist_ok=True)
            file = "{}/{}-{}.{}".format(save_location,file_name,last_modified.replace(':','-'),content_type)
            hash = md5(r.content)
            if add_to_db(hash,file_name):
                with open(file, 'wb') as f:
                    print("Downloading: {}".format(file))
                    f.write(r.content)








