import json
import re
import time
import urllib.parse
import webbrowser
import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = "dj0yJmk9cEJLYW9PaWRxQkFMJmQ9WVdvOVdsY0VWSGFFTWtTWmZtWkNWbnhzbzINQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTU4"
CLIENT_SECRET = "ec22ba8af8dff2fb8b888454e4772d247cfff73f"
REDIRECT_URI = "https://localhost:8550"

auth_url = (
    f"https://api.login.yahoo.com/oauth2/request_auth"
    f"?client_id={CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code"
)

print("\n1. Opening Yahoo Authorization page in your browser...")
webbrowser.open(auth_url)

print("\nIf the browser did not open automatically, copy and paste this link:")
print(auth_url)

print("\n2. Log in and click 'Agree' / 'Allow'.")
print("   Your browser will redirect to a page starting with https://localhost:8550/?code=...")
print("   (It is expected if your browser says 'Site cannot be reached'—the code is in the address bar).")

user_input = input("\n3. Paste the entire URL from your browser address bar here: ").strip()

match = re.search(r"code=([^&]+)", user_input)
code = match.group(1) if match else user_input

print("\nExchanging authorization code for tokens...")
token_url = "https://api.login.yahoo.com/oauth2/get_token"

response = requests.post(
    token_url,
    auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    },
)

if response.status_code == 200:
    data = response.json()
    oauth2_data = {
        "access_token": data["access_token"],
        "consumer_key": CLIENT_ID,
        "consumer_secret": CLIENT_SECRET,
        "refresh_token": data["refresh_token"],
        "token_time": time.time(),
        "token_type": "bearer",
    }
    with open("oauth2.json", "w", encoding="utf-8") as f:
        json.dump(oauth2_data, f, indent=4)
    print("\nSUCCESS: Fresh OAuth2 tokens saved to oauth2.json!")
else:
    print(f"\nERROR ({response.status_code}): {response.text}")