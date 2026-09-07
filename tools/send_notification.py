import os
import sys
import requests

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
ONESIGNAL_APP_ID = "bf74f838-0208-468e-81a2-0cc2be370b90"
APP_URL = "https://npk-dashboard-ug3g.onrender.com"

# Read key from local untracked file or environment variable
KEY_FILE = os.path.join(os.path.dirname(__file__), "onesignal_key.txt")
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        ONESIGNAL_REST_KEY = f.read().strip()
else:
    ONESIGNAL_REST_KEY = os.environ.get("ONESIGNAL_REST_KEY", "")


def send_push(title: str, message: str):
    if not ONESIGNAL_REST_KEY:
        print("[OneSignal] Push skipped: REST API Key not found in onesignal_key.txt or environment.")
        return

    url = "https://onesignal.com/api/v1/notifications"
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Total Subscriptions"],
        "headings": {"en": title},
        "contents": {"en": message},
        "url": APP_URL,
        "chrome_web_icon": f"{APP_URL}/icons/icon-192.png",
    }

    # Format 1: Key format
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Key {ONESIGNAL_REST_KEY}",
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[SUCCESS] Push notification broadcasted: {title}")
            return

        # Format 2: Bearer format
        headers["Authorization"] = f"Bearer {ONESIGNAL_REST_KEY}"
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[SUCCESS] Push notification broadcasted: {title}")
            return

        # Format 3: Basic format
        headers["Authorization"] = f"Basic {ONESIGNAL_REST_KEY}"
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[SUCCESS] Push notification broadcasted: {title}")
            return

        print(f"[ERROR] OneSignal response ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"[ERROR] Failed to send notification: {e}")


if __name__ == "__main__":
    notif_title = sys.argv[1] if len(sys.argv) > 1 else "NPK League Update"
    notif_body = sys.argv[2] if len(sys.argv) > 2 else "New weekly content has just been published!"
    send_push(notif_title, notif_body)