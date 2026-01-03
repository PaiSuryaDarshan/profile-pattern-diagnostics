from pathlib import Path
from ppd.cohort import materialise_db

# NOTE BUGFIX:
# tbd_manual_run.py lives at: src/ppd/cohort/tbd_manual_run.py
# Repo root is 4 levels up: cohort -> ppd -> src -> profile-pattern-diagnostics
REPO_ROOT = Path(__file__).resolve().parents[3]

IN_DB = REPO_ROOT / "examples" / "input" / "cohort_diverse_example.db"
OUT_DB = REPO_ROOT / "examples" / "output" / "cohort_diverse_final.db"

# Ensure output folder exists
OUT_DB.parent.mkdir(parents=True, exist_ok=True)

# if __name__ == "__main__":
#     materialise_db(
#         in_db=IN_DB,
#         out_db=OUT_DB,
#         store_json_reports=True,
#     )
#     print(f"✅ Wrote: {OUT_DB}")