import csv
import os
import re
from datetime import datetime
import utils.llm_utils as llm_utils
from fetch_data_user import fetch_user_data_for_specific_disorder, fetch_user_data_for_other_disorders
from utils.regex_utils import get_disorder_for_term
from agents.agent2_englishchecker import is_english
from utils.path_utils import RAW_PATH, OUTPUT_FILE, VERIFIED_USERS_FILE, USER_RECHECK_FILE, USER_RECHECK_OTHER_DISORDERS


def find_latest_raw_file(directory=RAW_PATH):
    """This function finds the most recent 'reddit_sz_posts_and_comments_YYYY-MM-DD_runX.csv' file."""
    files = os.listdir(directory)
    pattern = re.compile(r"reddit_sz_posts_and_comments_(\d{4}-\d{2}-\d{2})_run(\d+)\.csv")
    matches = []
    for fname in files:
        match = pattern.match(fname)
        if match:
            date_str, run_str = match.groups()
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            run_num = int(run_str)
            matches.append((dt, run_num, fname))
    if not matches:
        raise FileNotFoundError("No matching raw data files found.")
    latest_file = sorted(matches, reverse=True)[0][2]
    print(f"Agent 1 operating on: {latest_file}")
    return os.path.join(directory, latest_file)




def load_raw_posts(filepath):
    """Load raw posts and comments from initial subreddit data."""
    with open(filepath, newline='', encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_verified_users(filepath):
    """Load verified usernames from the CSV file."""
    verified_usernames = set()
    if not os.path.exists(filepath):
        open(filepath, 'w', newline='', encoding="utf-8").close()  # Create the file if it doesn't exist

    with open(filepath, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            verified_usernames.add(row[0])  # One-column file with usernames only
    return verified_usernames


def save_verified_user(username, filepath):
    """Save a single verified username to CSV."""
    with open(filepath, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([username])


def save_verified_post(post, writer):
    """Just a simple writer"""
    writer.writerow(post)


def run_agent_verify_disorder(disorder: str):
    RAW_FILE = find_latest_raw_file()
    print("Agent 1: Starting self-declaration verification")

    verified_usernames = load_verified_users(VERIFIED_USERS_FILE)
    raw_posts = load_raw_posts(RAW_FILE)
    users_to_recheck = set()
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    output_file_exists = os.path.exists(OUTPUT_FILE)

    # Ensuring that all columns match previous and future csv files
    expected_field_order = [
        "type", "id", "parent_id", "username", "user_flair", "created_utc",
        "title", "text", "score", "upvote_ratio", "num_comments", "subreddit",
        "flair_declared", "text_declared", "any_declared", "is_english", "llm_verified"
    ]

    # === Phase 1: Process raw posts ===
    with open(OUTPUT_FILE, "a", newline='', encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=expected_field_order, extrasaction="ignore")
        if not output_file_exists:
            writer.writeheader()

        for post in raw_posts:
            text_declared = post.get("text_declared", "").lower()
            # print(text_declared)
            flair_declared = post.get("flair_declared", "").lower()
            # print(flair_declared)

            if text_declared == "true":
                full_text = f"{post.get('title', '')}\n{post.get('text', '')}"
                # Calls agent2 to check English:
                if is_english(full_text):
                    post["is_english"] = True
                    result = llm_utils.verify_self_declaration_with_llm(full_text, disorder)
                    post["llm_verified"] = result
                    save_verified_post(post, writer)
                else:
                    post["is_english"] = False
            elif flair_declared == 'true' and text_declared != "true":
                username = post.get("username")
                if username and username not in verified_usernames:
                    users_to_recheck.add(username)

    # === Phase 2: Fetch and process users with flair-only declarations ===
    # If a user only has a flair declaration, then the code stores its username and pass it to fetch_data_user
    # fetch_data_user is a script to search the user's posts for more textual clues
    # This is important because textual explicit self-declaration are stronger than flairs

    if users_to_recheck:
        print(f"Fetching posts for {len(users_to_recheck)} flair-only users")
        fetch_user_data_for_specific_disorder(list(users_to_recheck), post_limit=None, disorder=disorder)

        # Ensure the correct file is referenced
        raw_recheck_file = USER_RECHECK_FILE
        if os.path.exists(raw_recheck_file):
            with open(OUTPUT_FILE, "a", newline='', encoding="utf-8") as out_f:
                writer = csv.DictWriter(out_f, fieldnames=expected_field_order, extrasaction="ignore")

                with open(raw_recheck_file, newline='', encoding="utf-8") as f_recheck:
                    recheck_posts = list(csv.DictReader(f_recheck))
                    for post in recheck_posts:
                        username = post.get("username")
                        if username in verified_usernames:
                            continue

                        text_declared = post.get("text_declared", "").lower()
                        if text_declared != 'true':
                            continue

                        full_text = f"{post.get('title', '')}\n{post.get('text', '')}"

                        # Calls agent2 to check English:
                        if is_english(full_text):
                            post["is_english"] = True
                            if llm_utils.verify_self_declaration_with_llm(full_text, disorder):
                                post["llm_verified"] = True
                                save_verified_post(post, writer)
                                verified_usernames.add(username)
                                save_verified_user(username, VERIFIED_USERS_FILE)
                            else:
                                post["llm_verified"] = False
                        else:
                            post["is_english"] = False

    print(f"Agent 1: Finished verifying self-declarations of {disorder}. Verified posts saved to {OUTPUT_FILE}")

import os
import csv

def run_agent_verify_other_disorders(users_to_recheck, verified_usernames, disorder):
    """
    Verifies self-declarations for disorders other than the specified one,
    by checking posts with patterns found in USER_RECHECK_OTHER_DISORDERS file,
    calling the LLM with the disorder found from the pattern.

    Parameters:
        users_to_recheck (set or list): Usernames to recheck.
        verified_usernames (set): Usernames already verified.
        disorder (str): The disorder to exclude (like 'sz').
    """

    expected_field_order = [
        "type", "id", "parent_id", "username", "user_flair", "created_utc",
        "title", "text", "score", "upvote_ratio", "num_comments", "subreddit",
        "flair_declared", "text_declared", "any_declared", "is_english", "llm_verified", "pattern_found"
    ]

    if os.path.exists(VERIFIED_USERS_FILE) and users_to_recheck:
        print(f"Fetching posts for {len(users_to_recheck)} flair-only users for disorders other than {disorder}")
        fetch_user_data_for_other_disorders(list(users_to_recheck), post_limit=None, disorder=disorder)

        raw_recheck_file = USER_RECHECK_OTHER_DISORDERS
        if os.path.exists(raw_recheck_file):
            with open(OUTPUT_FILE, "a", newline='', encoding="utf-8") as out_f:
                writer = csv.DictWriter(out_f, fieldnames=expected_field_order, extrasaction="ignore")

                with open(raw_recheck_file, newline='', encoding="utf-8") as f_recheck:
                    recheck_posts = list(csv.DictReader(f_recheck))
                    for post in recheck_posts:
                        username = post.get("username")
                        if username in verified_usernames:
                            continue

                        text_declared = post.get("text_declared", "").lower()
                        if text_declared != 'true':
                            continue

                        full_text = f"{post.get('title', '')}\n{post.get('text', '')}"

                        # Get disorder from pattern_found column
                        pattern_term = post.get("pattern_found", "")
                        detected_disorder = get_disorder_for_term(pattern_term)
                        if not detected_disorder:
                            continue  # skip if no disorder found

                        # Calls agent2 to check English and verify self-declaration for the detected disorder
                        if is_english(full_text):
                            post["is_english"] = True
                            if llm_utils.verify_self_declaration_with_llm(full_text, detected_disorder):
                                post["llm_verified"] = True
                                save_verified_post(post, writer)
                                verified_usernames.add(username)
                                save_verified_user(username, VERIFIED_USERS_FILE)
                            else:
                                post["llm_verified"] = False
                        else:
                            post["is_english"] = False

        print(f"Agent 1: Finished verifying self-declarations for disorders other than {disorder}. Verified posts saved to {OUTPUT_FILE}")
