import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DEBOUNCE_SECONDS = 5  # wait 5 seconds after last change

class GitAutoPush(FileSystemEventHandler):
    def __init__(self):
        self.last_event_time = time.time()
        self.pending = False

    def on_any_event(self, event):
        if event.is_directory:
            return
        self.last_event_time = time.time()
        self.pending = True

def git_commit_and_push():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(
            ["git", "commit", "-m", "Auto commit (debounced)"],
            check=True
        )
        subprocess.run(["git", "push"], check=True)
        print("✅ Debounced auto commit + push completed.")
    except subprocess.CalledProcessError:
        print("ℹ️ No changes to commit.")

if __name__ == "__main__":
    path = "."
    event_handler = GitAutoPush()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    print("👀 Watching for changes with debounce enabled...")

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
