import praw
import time
import re
import csv
import os
from utils.reddit_utils import get_reddit_instance
from datetime import datetime
import fetch_data_subreddit
import utils.regex_utils
from utils.regex_utils import find_all_but_one_patterns, get_flair_pattern_for_disorder
from utils.path_utils import RAW_PATH, OUTPUT_FILE, VERIFIED_USERS_FILE, USER_RECHECK_FILE, USER_RECHECK_OTHER_DISORDERS
from tqdm import tqdm

def fetch_user_data_for_specific_disorder(usernames, post_limit=None, delay=1.0, disorder=''):
    """
    Fetch submissions and comments for given usernames.
    Identify potential schizophrenia self-declarations via regex.
    Save results to 'data/raw/verified_users_step1_posts.csv'.

    Parameters:
        usernames (list): List of Reddit usernames.
        post_limit (int): Number of items to fetch per user per type.
        delay (float): Delay in seconds between each user fetch.
        disorder (int): acronym for disorder of choice
    """
    reddit = get_reddit_instance()
    collected = []

    for username in usernames:
        try:
            # print(f"🔍 Fetching history for u/{username}")
            user = reddit.redditor(username)

            # === Fetch submissions ===
            for submission in tqdm(user.submissions.new(limit=post_limit), desc=f"🔍 Posts from u/{username}"):
                user_flair = submission.author_flair_text if submission.author_flair_text else ""
                author_name = submission.author.name if submission.author else "deleted"
                pattern_flair = get_flair_pattern_for_disorder(disorder)
                flair_declared = bool(pattern_flair.search(user_flair))
                submission_declared = fetch_data_subreddit.match_self_declaration(submission.selftext + " " + submission.title, disorder)
                any_declared = flair_declared or submission_declared
                post_text = f"{submission.title}\n{submission.selftext or ''}"
                collected.append({
                    'type': 'submission',
                    'id': submission.id,
                    "parent_id": None,
                    'username': author_name,
                    'user_flair': submission.author_flair_text,
                    'created_utc': datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                    'title': submission.title,
                    'text': submission.selftext,
                    'score': submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    'subreddit': submission.subreddit.display_name,
                    "flair_declared": flair_declared,
                    "text_declared": submission_declared,
                    "any_declared": any_declared
                })

            # === Fetch comments ===
            for comment in tqdm(user.comments.new(limit=post_limit), desc=f"🔍 Comments from u/{username}"):
                comment_flair = comment.author_flair_text or ""
                pattern_flair = get_flair_pattern_for_disorder(disorder)
                flair_declared_c = bool(pattern_flair.search(comment_flair))
                comment_declared = fetch_data_subreddit.match_self_declaration(comment.body, disorder)
                any_declared_c = flair_declared_c or comment_declared
                if any_declared_c:
                    collected.append({
                        'type': 'comment',
                        'id': comment.id,
                        'parent_id': comment.parent_id,
                        'username': comment.author.name,
                        'user_flair': comment_flair,
                        'created_utc': datetime.utcfromtimestamp(comment.created_utc).isoformat(),
                        'title': '',
                        'text': comment.body,
                        'score': comment.score,
                        'upvote_ratio': None,
                        'num_comments': None,
                        'subreddit': comment.subreddit.display_name,
                        'flair_declared': flair_declared_c,
                        'text_declared': comment_declared,
                        'any_declared': any_declared_c
                    })

            time.sleep(delay)

        except Exception as e:
            print(f"⚠️ Could not fetch user u/{username}: {str(e)}")
            continue

    if collected:
        output_path = USER_RECHECK_FILE
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=collected[0].keys())
            writer.writeheader()
            writer.writerows(collected)
        print(f"✅ Saved {len(collected)} user posts/comments to {output_path}")
    else:
        print("⚠️ No data collected.")



def fetch_user_data_for_other_disorders(usernames, post_limit=None, delay=1.0, disorder=''):
    """
        Fetch submissions and comments for given usernames.
        Identify self-declarations for all disorders except the specified one.
        Save results to 'data/raw/verified_users_step1_posts.csv'.

        Parameters:
            usernames (list): List of Reddit usernames.
            post_limit (int): Number of items to fetch per user per type.
            delay (float): Delay in seconds between each user fetch.
            disorder (str): Disorder to exclude from pattern matching (e.g., 'sz')
    """
    reddit = get_reddit_instance()
    collected = []

    # Compile regex patterns for all disorders except the one specified
    patterns = find_all_but_one_patterns(disorder)

    def first_matching_pattern(text):
        for p in patterns:
            if p.search(text):
                return p.pattern  # returns the pattern string of the regex
        return None

    for username in usernames:
        try:
            print(f"🔍 Fetching history for u/{username}")
            user = reddit.redditor(username)

            # === Fetch submissions ===
            for submission in user.submissions.new(limit=post_limit):
                user_flair = submission.author_flair_text if submission.author_flair_text else ""
                author_name = submission.author.name if submission.author else "deleted"
                pattern_flair = get_flair_pattern_for_disorder(disorder)
                flair_declared = bool(pattern_flair.search(user_flair))

                full_text = submission.title + " " + (submission.selftext or "")
                pattern_found_in_text = first_matching_pattern(full_text)
                submission_declared = bool(pattern_found_in_text)

                any_declared = flair_declared or submission_declared

                collected.append({
                    'type': 'submission',
                    'id': submission.id,
                    "parent_id": None,
                    'username': author_name,
                    'user_flair': user_flair,
                    'created_utc': datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                    'title': submission.title,
                    'text': submission.selftext,
                    'score': submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    'subreddit': submission.subreddit.display_name,
                    "flair_declared": flair_declared,
                    "text_declared": submission_declared,
                    "any_declared": any_declared,
                    "pattern_found": pattern_found_in_text
                })

            # === Fetch comments ===
            for comment in user.comments.new(limit=post_limit):
                comment_flair = comment.author_flair_text or ""
                pattern_flair = get_flair_pattern_for_disorder(disorder)
                flair_declared_c = bool(pattern_flair.search(comment_flair))

                pattern_found_in_comment = first_matching_pattern(comment.body)
                comment_declared = bool(pattern_found_in_comment)

                any_declared_c = flair_declared_c or comment_declared

                if any_declared_c:
                    collected.append({
                        'type': 'comment',
                        'id': comment.id,
                        'parent_id': comment.parent_id,
                        'username': comment.author.name,
                        'user_flair': comment_flair,
                        'created_utc': datetime.utcfromtimestamp(comment.created_utc).isoformat(),
                        'title': '',
                        'text': comment.body,
                        'score': comment.score,
                        'upvote_ratio': None,
                        'num_comments': None,
                        'subreddit': comment.subreddit.display_name,
                        'flair_declared': flair_declared_c,
                        'text_declared': comment_declared,
                        'any_declared': any_declared_c,
                        'pattern_found': pattern_found_in_comment
                    })

            time.sleep(delay)

        except Exception as e:
            print(f"⚠️ Could not fetch user u/{username}: {str(e)}")
            continue

    if collected:
        output_path = USER_RECHECK_OTHER_DISORDERS
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=collected[0].keys())
            writer.writeheader()
            writer.writerows(collected)
        print(f"✅ Saved {len(collected)} user posts/comments to {output_path}")
    else:
        print("⚠️ No data collected.")
