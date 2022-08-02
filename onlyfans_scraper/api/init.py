r"""
               _          __                                                                      
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __ 
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |   
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|   
                  |___/                                                        |_|                
"""

import httpx

from ..constants import initEP
from ..utils import auth


def init_dummy_session(headers):
    original_id = headers['user-id']
    headers['user-id'] = '0'
    original_x_bc = headers.pop('x-bc')

    try:
        with httpx.Client(http2=True, headers=headers) as c:
            c.headers.update(auth.create_sign(initEP, headers))
            r = c.get(initEP, timeout=None)
            if not r.is_error:
                print('Status - \033[32mUP\033[0m')
            else:
                print('Status - \033[31mDOWN\033[0m')
    finally:
        headers['user-id'] = original_id
        headers['x-bc'] = original_x_bc
