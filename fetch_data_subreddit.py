import praw
import pandas as pd
import re
from datetime import datetime
from utils.reddit_utils import get_reddit_instance
import os
from utils.regex_utils import find_declaration_patterns
import utils.regex_utils
from  tqdm import tqdm

# Regular expressions for self-declarations, update as needed


def match_self_declaration(text: str, pattern_type: str = 'sz') -> bool:
    """
    Checks if any self-declaration pattern of a given type matches the input text.

    Parameters:
        text (str): The input text to check.
        pattern_type (str): Type of pattern to use ('sz', 'bp', etc.).

    Returns:
        bool: True if any pattern matches the text, False otherwise.
    """
    compiled_patterns = find_declaration_patterns(pattern_type)
    return any(pat.search(text) for pat in compiled_patterns)

# Function to fetch data from subreddits, check for regex and append everything to a csv file
def fetch_subreddit_data(subreddit_name: str,
                              submission_goal=int(),
                              comment_goal=int()):
    # submission_goal and comment_goal are int variables that specify how many subs and comments you want the code
    # to find with textual or flair declarations of schizophrenia

    reddit = get_reddit_instance()
    subreddit = reddit.subreddit(subreddit_name)

    print(f"Fetching posts and comments from r/{subreddit_name} until {submission_goal} submissions and {comment_goal} comments with identifications are found...")

    data = []
    submissions_found = 0
    comments_found = 0
    total_submissions = 0
    total_comments = 0

    progress_bar = tqdm(total=submission_goal + comment_goal, desc="Fetching data")

    for submission in subreddit.new(limit=None):
        if submissions_found >= submission_goal and comments_found >= comment_goal:
            break

        progress_bar.n = min(submission_goal, submissions_found) + min(comment_goal, comments_found)

        total_submissions += 1
        # print(f'Submissions checked in total: {total_submissions}')
        submission.comments.replace_more(limit=0)

        user_flair = submission.author_flair_text if submission.author_flair_text else ""
        author_name = submission.author.name if submission.author else "deleted"

        flair_declared = bool(re.search(r'schizo|psychosis', user_flair, flags=re.IGNORECASE))
        submission_declared = match_self_declaration(submission.selftext + " " + submission.title, 'sz')
        any_declared = flair_declared or submission_declared

        if any_declared and submissions_found < submission_goal:
            submissions_found += 1
            # if submissions_found > 0:
            #     print(f'FOUND {submissions_found} SUBMISSIONS')
            data.append({
                "type": "submission",
                "id": submission.id,
                "parent_id": None,
                "username": author_name,
                "user_flair": user_flair,
                "created_utc": datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                "title": submission.title,
                "text": submission.selftext,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "subreddit": subreddit_name,
                "flair_declared": flair_declared,
                "text_declared": submission_declared,
                "any_declared": any_declared
            })

        for comment in submission.comments:
            # print('Checking commments now.')
            total_comments += 1
            # print(f'Comments checked in total: {total_comments}')
            if comments_found >= comment_goal:
                break

            if comment.author:
                comment_author = comment.author.name
                comment_flair = comment.author_flair_text or ""
            else:
                comment_author = "deleted"
                comment_flair = ""

            flair_declared_c = bool(re.search(r'schizo|psychosis', comment_flair, flags=re.IGNORECASE))
            comment_declared = match_self_declaration(comment.body,'sz')
            any_declared_c = flair_declared_c or comment_declared

            if any_declared_c and comments_found < comment_goal:
                comments_found += 1
                # if comments_found > 0:
                #     print(f'FOUND {comments_found} COMMENTS')
                data.append({
                    "type": "comment",
                    "id": comment.id,
                    "parent_id": comment.parent_id,
                    "username": comment_author,
                    "user_flair": comment_flair,
                    "created_utc": datetime.utcfromtimestamp(comment.created_utc).isoformat(),
                    "title": "",
                    "text": comment.body,
                    "score": comment.score,
                    "upvote_ratio": None,
                    "num_comments": None,
                    "subreddit": subreddit_name,
                    "flair_declared": flair_declared_c,
                    "text_declared": comment_declared,
                    "any_declared": any_declared_c
                })

    df = pd.DataFrame(data)

    # Create output directory if it doesn't exist
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)

    # Generate base filename with today's date
    today = datetime.today().strftime("%Y-%m-%d")
    base_filename = f"reddit_sz_posts_and_comments_{today}"

    # Find next available run number
    run_number = 1
    while True:
        output_path = os.path.join(output_dir, f"{base_filename}_run{run_number}.csv")
        if not os.path.exists(output_path):
            break
        run_number += 1

    # Save to uniquely named file
    df.to_csv(output_path, index=False)

    # print(f"Finished fetching from subreddits.")
    print()
    print(f"Fetched {total_submissions} submissions and {total_comments} comments in total.")
    print(f"Kept {submissions_found} submissions and {comments_found} comments with self-identifications.")
    # print(f"Saved to {output_path}")
