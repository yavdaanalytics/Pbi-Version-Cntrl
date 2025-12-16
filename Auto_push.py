import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GitAutoPush(FileSystemEventHandler):
    def on_modified(self, event):
        print("Change detected. Committing...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto commit"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("Auto commit + push completed.")
        except:
            print("Nothing to commit or push failed.")

if __name__ == "__main__":
    path = "."
    event_handler = GitAutoPush()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    
    print("Watching for changes... Auto Git enabled.")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
