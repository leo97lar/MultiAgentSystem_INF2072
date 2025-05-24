from pathlib import Path
project_root = Path(__file__).parent.parent.resolve().__str__()
USER_RECHECK_OTHER_DISORDERS = project_root + '/data/raw/user_recheck_other_disorders.csv'
USER_RECHECK_FILE = project_root + '/data/raw/user_recheck.csv' # Users that agent1 flagged "No" for self-declaration
OUTPUT_FILE = project_root + '/data/processed/verified_self_declarations.csv' # Self-declarations that agent1 flagged "Yes"
VERIFIED_USERS_FILE = project_root + '/data/processed/verified_users.csv' # Username that agent1 flagged "Yes" for self-declarations
RAW_PATH = project_root + '/data/raw/' # Path to files that did not go through agents yet
