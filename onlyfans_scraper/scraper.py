r"""
               _          __                                                                      
  ___   _ __  | | _   _  / _|  __ _  _ __   ___         ___   ___  _ __   __ _  _ __    ___  _ __ 
 / _ \ | '_ \ | || | | || |_  / _` || '_ \ / __| _____ / __| / __|| '__| / _` || '_ \  / _ \| '__|
| (_) || | | || || |_| ||  _|| (_| || | | |\__ \|_____|\__ \| (__ | |   | (_| || |_) ||  __/| |   
 \___/ |_| |_||_| \__, ||_|   \__,_||_| |_||___/       |___/ \___||_|    \__,_|| .__/  \___||_|   
                  |___/                                                        |_|                
"""

import argparse
import asyncio
import datetime
import os
import sys
import platform
from random import randint, choice
from time import sleep
from datetime import datetime, timedelta

from .api import init, highlights, me, messages, posts, profile, subscriptions
from .db import operations
from .interaction import like
from .utils import auth, config, download, profiles, prompts

from revolution import Revolution


# silent = False
#
# def need_revolution(message):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             if silent:
#                 func(*args, **kwargs)
#             if not silent:
#                 @Revolution(desc=message)
#                 def dec(*args,**kwargs):
#                     func(*args, **kwargs)
#                 return dec(*args, **kwargs)
#
#         return wrapper
#     return decorator




# @need_revolution("Getting messages...")
@Revolution(desc='Getting messages...')
def process_messages(headers, model_id):
    messages_ = messages.scrape_messages(headers, model_id)

    if messages_:
        messages_urls = messages.parse_messages(messages_, model_id)
        return messages_urls
    return []

# @need_revolution("Getting highlights...")
@Revolution(desc='Getting highlights...')
def process_highlights(headers, model_id):
    highlights_, stories = highlights.scrape_highlights(headers, model_id)

    if highlights_ or stories:
        highlights_ids = highlights.parse_highlights(highlights_)
        stories += asyncio.run(
            highlights.process_highlights_ids(headers, highlights_ids))
        stories_urls = highlights.parse_stories(stories)
        return stories_urls
    return []

# @need_revolution("Getting subscriptions...")
@Revolution(desc='Getting archived media...')
def process_archived_posts(headers, model_id):
    archived_posts = posts.scrape_archived_posts(headers, model_id)

    if archived_posts:
        archived_posts_urls = posts.parse_posts(archived_posts)
        return archived_posts_urls
    return []

# @need_revolution("Getting timeline media...")
@Revolution(desc='Getting timeline media...')
def process_timeline_posts(headers, model_id):
    timeline_posts = posts.scrape_timeline_posts(headers, model_id)

    if timeline_posts:
        timeline_posts_urls = posts.parse_posts(timeline_posts)
        return timeline_posts_urls
    return []

# @need_revolution("Getting pinned media...")
@Revolution(desc='Getting pinned media...')
def process_pinned_posts(headers, model_id):
    pinned_posts = posts.scrape_pinned_posts(headers, model_id)

    if pinned_posts:
        pinned_posts_urls = posts.parse_posts(pinned_posts)
        return pinned_posts_urls
    return []


def process_profile(headers, username) -> list:
    user_profile = profile.scrape_profile(headers, username)
    urls, info = profile.parse_profile(user_profile)
    profile.print_profile_info(info)
    return urls


def process_areas_all(headers, username, model_id) -> list:
    profile_urls = process_profile(headers, username)

    pinned_posts_urls = process_pinned_posts(headers, model_id)
    timeline_posts_urls = process_timeline_posts(headers, model_id)
    archived_posts_urls = process_archived_posts(headers, model_id)
    highlights_urls = process_highlights(headers, model_id)
    messages_urls = process_messages(headers, model_id)

    combined_urls = profile_urls + pinned_posts_urls + timeline_posts_urls + \
        archived_posts_urls + highlights_urls + messages_urls

    return combined_urls


def process_areas(headers, username, model_id) -> list:
    result_areas_prompt = prompts.areas_prompt()

    if 'All' in result_areas_prompt:
        combined_urls = process_areas_all(headers, username, model_id)

    else:
        pinned_posts_urls = []
        timeline_posts_urls = []
        archived_posts_urls = []
        highlights_urls = []
        messages_urls = []

        profile_urls = process_profile(headers, username)

        if 'Timeline' in result_areas_prompt:
            pinned_posts_urls = process_pinned_posts(headers, model_id)
            timeline_posts_urls = process_timeline_posts(headers, model_id)

        if 'Archived' in result_areas_prompt:
            archived_posts_urls = process_archived_posts(headers, model_id)

        if 'Highlights' in result_areas_prompt:
            highlights_urls = process_highlights(headers, model_id)

        if 'Messages' in result_areas_prompt:
            messages_urls = process_messages(headers, model_id)

        combined_urls = profile_urls + pinned_posts_urls + timeline_posts_urls + \
            archived_posts_urls + highlights_urls + messages_urls

    return combined_urls


def do_download_content(headers, username, model_id, ignore_prompt=False):
    # If we should ignore the process_areas prompt:
    if ignore_prompt:
        combined_urls = process_areas_all(headers, username, model_id)
    # Otherwise, display the prompt to the user
    else:
        combined_urls = process_areas(headers, username, model_id)
    # If we shouldn't ignore the areas prompt:

    asyncio.run(download.process_urls(
        headers,
        username,
        model_id,
        combined_urls))


def do_database_migration(path, model_id):
    results = operations.read_foreign_database(path)
    operations.write_from_foreign_database(results, model_id)


def get_usernames(parsed_subscriptions: list) -> list:
    usernames = [sub[0] for sub in parsed_subscriptions]
    return usernames


def get_model(parsed_subscriptions: list) -> tuple:
    """
    Prints user's subscriptions to console and accepts input from user corresponding 
    to the model whose content they would like to scrape.
    """
    subscriptions.print_subscriptions(parsed_subscriptions)

    print('\nEnter the number next to the user whose content you would like to download:')
    while True:
        try:
            num = int(input('> '))
            return parsed_subscriptions[num - 1]
        except ValueError:
            print("Incorrect value. Please enter an actual number.")
        except IndexError:
            print("Value out of range. Please pick a number that's in range")


def get_models(headers, subscribe_count) -> list:
    """
    Get user's subscriptions in form of a list.
    """
    with Revolution(desc='Getting your subscriptions (this may take awhile)...') as _:
        list_subscriptions = asyncio.run(
            subscriptions.get_subscriptions(headers, subscribe_count))
        parsed_subscriptions = subscriptions.parse_subscriptions(
            list_subscriptions)
    return parsed_subscriptions


def process_me(headers):
    my_profile = me.scrape_user(headers)
    name, username, subscribe_count = me.parse_user(my_profile)
    me.print_user(name, username)
    return subscribe_count


def process_prompts():
    loop = process_prompts

    profiles.print_current_profile()
    headers = auth.make_headers(auth.read_auth())
    init.print_sign_status(headers)

    result_main_prompt = prompts.main_prompt()

    if result_main_prompt == 0:
        # Download content from user
        result_username_or_list_prompt = prompts.username_or_list_prompt()

        # Print a list of users:
        if result_username_or_list_prompt == 0:
            subscribe_count = process_me(headers)
            parsed_subscriptions = get_models(headers, subscribe_count)
            username, model_id, *_ = get_model(parsed_subscriptions)

            do_download_content(headers, username, model_id)

        # Ask for a username to be entered:
        elif result_username_or_list_prompt == 1:
            username = prompts.username_prompt()
            model_id = profile.get_id(headers, username)

            do_download_content(headers, username, model_id)

        else:
            # Ask if we should scrape all users
            result_verify_all_users = prompts.verify_all_users_username_or_list_prompt()
            # If we should, then:
            if result_verify_all_users:
                subscribe_count = process_me(headers)
                parsed_subscriptions = get_models(headers, subscribe_count)
                usernames = get_usernames(parsed_subscriptions)

                for username in usernames:
                    model_id = profile.get_id(headers, username)
                    do_download_content(
                        headers, username, model_id, ignore_prompt=True)

    elif result_main_prompt == 1:
        # Like a user's posts
        username = prompts.username_prompt()
        model_id = profile.get_id(headers, username)

        posts = like.get_posts(headers, model_id)
        unfavorited_posts = like.filter_for_unfavorited(posts)
        post_ids = like.get_post_ids(unfavorited_posts)
        like.like(headers, model_id, username, post_ids)

    elif result_main_prompt == 2:
        # Unlike a user's posts
        username = prompts.username_prompt()
        model_id = profile.get_id(headers, username)

        posts = like.get_posts(headers, model_id)
        favorited_posts = like.filter_for_favorited(posts)
        post_ids = like.get_post_ids(favorited_posts)
        like.unlike(headers, model_id, username, post_ids)

    elif result_main_prompt == 3:
        # Migrate from old database
        path, username = prompts.database_prompt()
        model_id = profile.get_id(headers, username)
        do_database_migration(path, model_id)

        loop()

    elif result_main_prompt == 4:
        # Edit `auth.json` file
        auth.edit_auth()

        loop()

    elif result_main_prompt == 5:
        # Edit `config.json` file
        config.edit_config()

        loop()

    elif result_main_prompt == 6:
        # Display  `Profiles` menu
        result_profiles_prompt = prompts.profiles_prompt()

        if result_profiles_prompt == 0:
            # Change profiles
            profiles.change_profile()

        if result_profiles_prompt == 1:
            # Edit a profile
            profiles_ = profiles.get_profiles()

            old_profile_name = prompts.edit_profiles_prompt(profiles_)
            new_profile_name = prompts.new_name_edit_profiles_prompt(
                old_profile_name)

            profiles.edit_profile_name(old_profile_name, new_profile_name)

        elif result_profiles_prompt == 2:
            # Create a new profile
            profile_path = profiles.get_profile_path()
            profile_name = prompts.create_profiles_prompt()

            profiles.create_profile(profile_path, profile_name)

        elif result_profiles_prompt == 3:
            # Delete a profile
            profiles.delete_profile()

        elif result_profiles_prompt == 4:
            # View profiles
            profiles.print_profiles()

        loop()

def download_user(username):
    headers = auth.make_headers(auth.read_auth())
    do_download_content(headers, username, profile.get_id(headers, username), ignore_prompt=True)



def silent_run():
    headers = auth.make_headers(auth.read_auth())

    try:
        resp = me.scrape_user(headers)
    except Exception as e:
        print("Silent run failed with exception: ", e)
        return
    subscribe_count = process_me(headers)
    parsed_subscriptions = get_models(headers, subscribe_count)
    usernames = get_usernames(parsed_subscriptions)

    for username in usernames:
        model_id = profile.get_id(headers, username)
        do_download_content(
            headers, username, model_id, ignore_prompt=True)


def daemon():
    has_gone_night_night = False
    night_night_timer = datetime.datetime.now()
    waking_up = False
    while True:
        # Trying vs running allows the daemon to recover from errors and try again later.
        try:
            silent_run()
        except Exception as e:
            print("Daemon failed with exception: ", e)
        finally:
            # If the daemon has not paused for a normal person sleep cycle (7 - 9 hours)
            # in the last 14 hours it will sleep for 7 - 9 hours.
            if not has_gone_night_night:
                if night_night_timer - datetime.datetime.now() > timedelta(hours=14):
                    has_gone_night_night = True
                    t = choice([x for x in range(25200, 32400)])
                    print("Going night night for {} hours".format(t/3600))
                    sleep(t)
                    night_night_timer = datetime.datetime.now()
                    waking_up = True

            if not waking_up:
                # Sleep for between 1 and 2 hours
                t1 = randint(3600, 7200)
                # t2 is an offset that can be anywhere from 0 to 30 minutes
                t2 = randint(0, 1800)
                # This allows us to sleep for a random amount of time between 1 and 2.5 hours.
                # This helps to prevent the daemon from being detected by the site as a bot.
                # To my knowledge, this type of detection isn't used by the site, but it's
                # better to be safe than sorry.
                t = t1 + t2
                sleep(t)
            else:
                waking_up = False


def main():
    if platform.system == 'Windows':
        os.system('color')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-e', '--edit', help='view or edit your current auth', action='store_true')
    parser.add_argument(
        '-u', '--username', help="Download content from a user or list of users (name,name2)"
    )
    parser.add_argument(
        '-a', '--all', help='scrape the content of all users', action='store_true')
    parser.add_argument(
        '-d', '--daemon', help='This will run the program in the background and scrape everything from everyone. It will run untill manually killed.', action='store_true')

    args = parser.parse_args()
    if args.edit:
        pass
    if args.username:
        usernames = args.username
        for username in usernames.strip().split(','):
            download_user(username)
        sys.exit()
    if args.all:
        silent = True
        silent_run()
        sys.exit()
    if args.daemon:
        daemon()


    try:
        process_prompts()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()
