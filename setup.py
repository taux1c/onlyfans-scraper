r"""
               _          __                                                                      
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __ 
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |   
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|   
                  |___/                                                        |_|                
"""

import os
import platform
import setuptools

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
]

main = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(main, 'requirements.txt'), 'r', encoding='utf-8') as f:
    requirements = f.read().splitlines()
    if platform.system() != 'Windows':
        requirements.remove('win32_setctime')

about = {}
with open(os.path.join(main, 'onlyfans_scraper', '__version__.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), about)

setuptools.setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=about['__url__'],
    license=about['__license__'],
    packages=setuptools.find_packages(),
    classifiers=classifiers,
    keywords=['onlyfans', 'download', 'photos', 'videos', 'like'],
    install_requires=requirements,
    python_requires=">=3.8",
    zip_safe=False,
    entry_points={
        'console_scripts': ['onlyfans-scraper=onlyfans_scraper.scraper:main']
    },
    project_urls={
        'Source': 'https://github.com/Amenly/onlyfans-scraper'
    }
)
