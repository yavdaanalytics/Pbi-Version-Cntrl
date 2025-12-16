import time
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DEBOUNCE_SECONDS = 5
WATCH_PATH = "."

# --------------------------------------------------
# FILE WATCHER
# --------------------------------------------------
class GitAutoPush(FileSystemEventHandler):
    def __init__(self):
        self.last_event_time = time.time()
        self.pending = False

    def on_any_event(self, event):
        if event.is_directory:
            return
        self.last_event_time = time.time()
        self.pending = True


# --------------------------------------------------
# STEP 1: Detect changed files
# --------------------------------------------------
def get_changed_files():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    files = []
    for line in result.stdout.splitlines():
        files.append(line[3:])
    return files


# --------------------------------------------------
# STEP 2: Classify PBIP changes
# --------------------------------------------------
def classify_changes(files):
    summary = {
        "measures": [],
        "tables": [],
        "relationships": [],
        "visuals": [],
        "other": []
    }

    for f in files:
        lf = f.lower()
        if "measures" in lf:
            summary["measures"].append(f)
        elif "tables" in lf:
            summary["tables"].append(f)
        elif "relationship" in lf:
            summary["relationships"].append(f)
        elif "visual" in lf or "report" in lf:
            summary["visuals"].append(f)
        else:
            summary["other"].append(f)

    return summary


# --------------------------------------------------
# STEP 3: Generate meaningful commit message
# --------------------------------------------------
def generate_commit_message(summary):
    lines = ["PBIP auto update:"]

    if summary["measures"]:
        lines.append(f"- Measures updated ({len(summary['measures'])})")
    if summary["tables"]:
        lines.append(f"- Tables modified ({len(summary['tables'])})")
    if summary["relationships"]:
        lines.append("- Relationships updated")
    if summary["visuals"]:
        lines.append("- Report visuals / layout changed")
    if summary["other"]:
        lines.append(f"- Other changes ({len(summary['other'])})")

    return "\n".join(lines)


# --------------------------------------------------
# STEP 4: Extract DAX / TMDL diff (learning audit)
# --------------------------------------------------
def get_diff(file):
    result = subprocess.run(
        ["git", "diff", "--", file],
        capture_output=True,
        text=True
    )
    return result.stdout[:1000]  # safety limit


# --------------------------------------------------
# STEP 5: Write CHANGELOG.md
# --------------------------------------------------
def update_changelog(summary, files):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("CHANGELOG.md", "a", encoding="utf-8") as f:
        f.write(f"\n## {timestamp}\n")

        if summary["measures"]:
            f.write("- Measures updated:\n")
            for m in summary["measures"]:
                f.write(f"  - {m}\n")

        if summary["tables"]:
            f.write("- Tables modified:\n")
            for t in summary["tables"]:
                f.write(f"  - {t}\n")

        if summary["relationships"]:
            f.write("- Relationships updated\n")

        if summary["visuals"]:
            f.write("- Visuals / report layout changed\n")

        if summary["other"]:
            f.write("- Other changes:\n")
            for o in summary["other"]:
                f.write(f"  - {o}\n")

        # Optional diff preview
        for file in files:
            if file.endswith((".dax", ".tmdl")):
                diff = get_diff(file)
                if diff:
                    f.write(f"\n<details>\n<summary>Diff: {file}</summary>\n\n")
                    f.write("```diff\n")
                    f.write(diff)
                    f.write("\n```\n</details>\n")


# --------------------------------------------------
# STEP 6: Commit & push
# --------------------------------------------------
def git_commit_and_push():
    files = get_changed_files()
    if not files:
        print("ℹ️ No changes to commit.")
        return

    summary = classify_changes(files)
    commit_msg = generate_commit_message(summary)

    try:
        update_changelog(summary, files)

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)

        print("✅ PBIP smart commit pushed:")
        print(commit_msg)

    except subprocess.CalledProcessError as e:
        print("❌ Git operation failed:", e)


# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
if __name__ == "__main__":
    event_handler = GitAutoPush()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=True)
    observer.start()

    print("👀 Watching PBIP changes with smart versioning enabled...")

    try:
        while True:
            time.sleep(1)
            if event_handler.pending:
                elapsed = time.time() - event_handler.last_event_time
                if elapsed >= DEBOUNCE_SECONDS:
                    git_commit_and_push()
                    event_handler.pending = False
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
