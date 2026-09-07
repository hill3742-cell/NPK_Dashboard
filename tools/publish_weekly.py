import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from datetime import datetime

# Import the existing notification engine
from send_notification import send_push

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_WEEKLY_DIR = os.path.join(BASE_DIR, "assets", "weekly")

def publish_weekly():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    current_year = datetime.now().year

    # 1. Ask for Season Year
    year = simpledialog.askinteger("Publish Weekly", "Enter Season Year:", initialvalue=current_year, minvalue=2010, maxvalue=2050)
    if not year:
        return

    # 2. Ask for Week Number
    week = simpledialog.askinteger("Publish Weekly", "Enter Week Number:", initialvalue=1, minvalue=1, maxvalue=25)
    if not week:
        return

    # 3. Ask for Type (Preview or Recap)
    choice = messagebox.askyesnocancel("Content Type", "Click [YES] for Preview\nClick [NO] for Recap")
    if choice is None:
        return
    content_type = "Preview" if choice else "Recap"

    # 4. Select the Draft/Source Text File
    messagebox.showinfo("Select Draft", f"Select your text or markdown file for Week {week} {content_type}.")
    file_path = filedialog.askopenfilename(
        title=f"Select Week {week} {content_type} File",
        filetypes=[("Text & Markdown Files", "*.txt *.md"), ("All Files", "*.*")]
    )
    if not file_path:
        return

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read().strip()

    # 5. Save directly into assets/weekly/
    os.makedirs(ASSETS_WEEKLY_DIR, exist_ok=True)
    target_filename = f"{year}_Week_{week:02d}_{content_type.lower()}.md"
    target_path = os.path.join(ASSETS_WEEKLY_DIR, target_filename)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Saved to {target_path}")

    # 6. Ask for Notification Details
    default_title = f"NPK Week {week} {content_type} is Live!"
    default_msg = f"Check out the latest Week {week} {content_type.lower()} on the league dashboard."

    custom_title = simpledialog.askstring("Push Notification", "Notification Title:", initialvalue=default_title)
    if not custom_title:
        custom_title = default_title

    custom_msg = simpledialog.askstring("Push Notification", "Notification Message:", initialvalue=default_msg)
    if not custom_msg:
        custom_msg = default_msg

    # 7. Git Commit & Push
    print("[Git] Staging and pushing changes to GitHub...")
    try:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        commit_msg = f"Publish {year} Week {week} {content_type}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=True)
        print("[Git] Successfully pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Git Error", f"Failed to push to GitHub:\n{e}")
        return

    # 8. Send OneSignal Push Notification
    print("[OneSignal] Broadcasting push notification...")
    send_push(custom_title, custom_msg)

    messagebox.showinfo(
        "Published Successfully",
        f"Week {week} {content_type} published to GitHub and push notification sent to the league!"
    )

if __name__ == "__main__":
    publish_weekly()