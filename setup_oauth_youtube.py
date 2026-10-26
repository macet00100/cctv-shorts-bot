"""
YouTube OAuth2 Permanent Refresh Token Generator
Run this script ONCE locally on your machine to authorize your YouTube channel:
    python setup_oauth_youtube.py

Prerequisites:
1. Create a Google Cloud Project at https://console.cloud.google.com/
2. Enable 'YouTube Data API v3'.
3. Create OAuth 2.0 Client ID (Application type: Desktop App).
4. Download or copy Client ID and Client Secret.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube"
]

def main():
    print("=" * 70)
    print("🔐 YOUTUBE OAUTH2 REFRESH TOKEN GENERATOR")
    print("=" * 70)

    client_id = input("\n👉 Enter your YOUTUBE_CLIENT_ID: ").strip()
    client_secret = input("👉 Enter your YOUTUBE_CLIENT_SECRET: ").strip()

    if not client_id or not client_secret:
        print("\n❌ Client ID and Client Secret cannot be empty!")
        return

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    print("\n🌐 Opening browser for Google Account authentication...")
    print("Please select your Google account and grant YouTube permissions.")

    credentials = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    refresh_token = credentials.refresh_token

    print("\n" + "=" * 70)
    print("🎉 AUTHENTICATION SUCCESSFUL!")
    print("=" * 70)
    print("\nCopy the following values and add them to your GitHub Secrets / .env:\n")
    print(f"YOUTUBE_CLIENT_ID={client_id}")
    print(f"YOUTUBE_CLIENT_SECRET={client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
