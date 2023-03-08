r"""
               _          __                                                                      
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __ 
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |   
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|   
                  |___/                                                        |_|                
"""

import asyncio
import math
import pathlib
import platform
import sys

import httpx
from tqdm.asyncio import tqdm
try:
    from win32_setctime import setctime  # pylint: disable=import-error
except ModuleNotFoundError:
    pass

from .auth import add_cookies
from .config import read_config
from .dates import convert_date_to_timestamp
from .separate import separate_by_id
from ..db import operations


async def process_urls(headers, username, model_id, urls):
    if urls:
        operations.create_database(model_id)
        media_ids = operations.get_media_ids(model_id)
        separated_urls = separate_by_id(urls, media_ids)

        config = read_config()['config']

        save_location = config.get('save_location')
        if save_location:
            try:
                dir = pathlib.Path(save_location)
            except:
                print(f"Unable to find save location. Using current working directory. ({pathlib.Path.cwd()})")
        else:
            dir = pathlib.Path.cwd()
        try:
            path = dir / username
            path.mkdir(exist_ok=True, parents=True)
        except:
            print("Error saving to save directory, check the directory and make sure correct permissions have been issued.")
            sys.exit()
        file_size_limit = config.get('file_size_limit')

        # Added pool limit:
        limits = httpx.Limits(max_connections=8, max_keepalive_connections=5)
        async with httpx.AsyncClient(headers=headers, limits=limits, timeout=None) as c:
            add_cookies(c)

            aws = [asyncio.create_task(
                download(c, path, model_id, file_size_limit, *url)) for url in separated_urls]

            photo_count = 0
            video_count = 0
            skipped = 0
            total_bytes_downloaded = 0
            data = 0

            desc = 'Progress: ({p_count} photos, {v_count} videos, {skipped} skipped || {data})'

            with tqdm(desc=desc.format(p_count=photo_count, v_count=video_count, skipped=skipped, data=data), total=len(aws), colour='cyan', leave=True) as main_bar:
                for coro in asyncio.as_completed(aws):
                    try:
                        media_type, num_bytes_downloaded = await coro
                    except Exception as e:
                        media_type = None
                        num_bytes_downloaded = 0
                        print(e)

                    total_bytes_downloaded += num_bytes_downloaded
                    data = convert_num_bytes(total_bytes_downloaded)

                    if media_type == 'photo':
                        photo_count += 1
                        main_bar.set_description(
                            desc.format(
                                p_count=photo_count, v_count=video_count, skipped=skipped, data=data), refresh=False)

                    elif media_type == 'video':
                        video_count += 1
                        main_bar.set_description(
                            desc.format(
                                p_count=photo_count, v_count=video_count, skipped=skipped, data=data), refresh=False)

                    elif media_type == 'skipped':
                        skipped += 1
                        main_bar.set_description(
                            desc.format(
                                p_count=photo_count, v_count=video_count, skipped=skipped, data=data), refresh=False)

                    main_bar.update()


def convert_num_bytes(num_bytes: int) -> str:
    if num_bytes == 0:
      return '0 B'
    num_digits = int(math.log10(num_bytes)) + 1

    if num_digits >= 10:
        return f'{round(num_bytes / 10**9, 2)} GB'
    return f'{round(num_bytes / 10 ** 6, 2)} MB'


async def download(client, path, model_id, file_size_limit,
                   url, date=None, id_=None, media_type=None):
    filename = url.split('?', 1)[0].rsplit('/', 1)[-1]
    path_to_file = path / filename
    #path_to_file = config.path_to_file
    #num_bytes_downloaded = 0

    async with client.stream('GET', url) as r:
        if not r.is_error:
            total = int(r.headers['Content-Length'])
            if file_size_limit:
                if total > int(file_size_limit):
                    return 'skipped', 1

            with tqdm(desc=filename, total=total, unit_scale=True, unit_divisor=1024, unit='B', leave=False) as bar:
                num_bytes_downloaded = r.num_bytes_downloaded
                with open(path_to_file, 'wb') as f:
                    async for chunk in r.aiter_bytes(chunk_size=1024):
                        f.write(chunk)
                        bar.update(
                            r.num_bytes_downloaded - num_bytes_downloaded)
                        num_bytes_downloaded = r.num_bytes_downloaded

        else:
            r.raise_for_status()

    if path_to_file.is_file():
        if date:
            set_time(path_to_file, convert_date_to_timestamp(date))

        if id_:
            data = (id_, filename)
            operations.write_from_data(data, model_id)

    return media_type, num_bytes_downloaded


def set_time(path, timestamp):
    if platform.system() == 'Windows':
        setctime(path, timestamp)
    pathlib.os.utime(path, (timestamp, timestamp))


def get_error_message(content):
    error_content = content.get('error', 'No error message available')
    try:
        return error_content.get('message', 'No error message available')
    except AttributeError:
        return error_content
