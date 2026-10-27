import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import (
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    YOUTUBE_REFRESH_TOKEN
)

class YouTubeShortsUploader:
    """
    Automated YouTube Shorts Uploader.
    Uses OAuth 2.0 Refresh Token for headless CI/CD deployment on GitHub Actions.
    Includes auto-like and auto-comment features.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube"
    ]

    def __init__(self):
        self.client_id = YOUTUBE_CLIENT_ID
        self.client_secret = YOUTUBE_CLIENT_SECRET
        self.refresh_token = YOUTUBE_REFRESH_TOKEN

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def _get_service(self):
        creds = Credentials(
            None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES
        )
        return build("youtube", "v3", credentials=creds)

    def upload(self, video_path: Path, scenario: Dict[str, Any]) -> Optional[str]:
        if not self.is_configured():
            print("[YOUTUBE] Credentials missing. Skipping YouTube Shorts upload.")
            return None

        try:
            youtube = self._get_service()

            raw_title = scenario.get("case_title", "Unexplained Surveillance Anomaly")
            title = f"{raw_title} #shorts #cctv #viral"[:100]

            tags = scenario.get("youtube_tags", ["shorts", "cctv", "caughtoncamera", "viral"])
            description = ""

            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "24",  # Entertainment
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            }

            media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)

            print(f"[YOUTUBE] Uploading Shorts video: {title}...")
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"[YOUTUBE] Upload progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            print(f"[YOUTUBE] Video uploaded successfully! Video ID: {video_id}")
            print(f"[YOUTUBE] Link: https://youtube.com/shorts/{video_id}")

            return video_id

        except Exception as e:
            print(f"[YOUTUBE] Upload failed: {e}")
            return None
