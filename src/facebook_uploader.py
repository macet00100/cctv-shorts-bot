import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests

from src.config import FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN

class FacebookReelsUploader:
    """
    Automated Facebook Reels Uploader using Graph API v19.0+.
    Uses Permanent Page Access Token (expires_at: 0) for zero-maintenance cloud publishing.
    Includes auto-like and auto-comment features.
    """

    GRAPH_VERSION = "v19.0"

    def __init__(self):
        self.page_id = FB_PAGE_ID
        self.access_token = FB_PAGE_ACCESS_TOKEN

    def is_configured(self) -> bool:
        return bool(self.page_id and self.access_token)

    def upload(self, video_path: Path, scenario: Dict[str, Any]) -> Optional[str]:
        if not self.is_configured():
            print("[FACEBOOK] Page ID or Token missing. Skipping Facebook Reels upload.")
            return None

        try:
            case_title = scenario.get("case_title", "Unexplained Camera Incident")
            pinned_comment_text = scenario.get("pinned_comment", "Real or staged? Tell us below 👇")
            description = f"""{case_title}

📍 Location: {scenario.get('hud_text_location', 'Restricted Area')}
📹 Perspective: {scenario.get('camera_mode', 'CCTV')}

What do you think is happening here?

#reels #caughtoncamera #cctv #foundfootage #mystery #paranormal #dashcam #bodycam
"""

            file_size = os.path.getsize(video_path)
            print(f"[FACEBOOK] Starting Facebook Reel upload: {case_title} ({file_size / 1024 / 1024:.2f} MB)...")

            # Phase 1: Initialize Reel Upload Session
            init_url = f"https://graph.facebook.com/{self.GRAPH_VERSION}/{self.page_id}/video_reels"
            init_res = requests.post(
                init_url,
                data={
                    "upload_phase": "start",
                    "access_token": self.access_token
                },
                timeout=30
            )
            init_data = init_res.json()

            if "video_id" not in init_data or "upload_url" not in init_data:
                print(f"[FACEBOOK] Init failed: {init_data}")
                return None

            video_id = init_data["video_id"]
            upload_url = init_data["upload_url"]
            print(f"[FACEBOOK] Session initialized. Video ID: {video_id}")

            # Phase 2: Binary Video Data Upload
            with open(video_path, "rb") as vf:
                video_bytes = vf.read()

            upload_headers = {
                "Authorization": f"OAuth {self.access_token}",
                "offset": "0",
                "file_size": str(file_size),
                "Content-Type": "application/octet-stream"
            }

            upload_res = requests.post(
                upload_url,
                headers=upload_headers,
                data=video_bytes,
                timeout=120
            )

            if upload_res.status_code not in (200, 201):
                print(f"[FACEBOOK] Upload binary failed ({upload_res.status_code}): {upload_res.text}")
                return None

            # Phase 3: Finalize & Publish Reel
            finish_url = f"https://graph.facebook.com/{self.GRAPH_VERSION}/{self.page_id}/video_reels"
            finish_res = requests.post(
                finish_url,
                data={
                    "upload_phase": "finish",
                    "video_id": video_id,
                    "video_state": "PUBLISHED",
                    "description": description,
                    "access_token": self.access_token
                },
                timeout=30
            )
            finish_data = finish_res.json()

            if finish_data.get("success") is True or "id" in finish_data or "video_id" in finish_data:
                print(f"[FACEBOOK] Reel successfully published! Video ID: {video_id}")
            else:
                print(f"[FACEBOOK] Finish response: {finish_data}")

            # Phase 4: Auto-like & Auto-comment
            time.sleep(2)
            self._auto_like(video_id)
            self._auto_comment(video_id, pinned_comment_text)

            return video_id

        except Exception as e:
            print(f"[FACEBOOK] Upload error: {e}")
            return None

    def _auto_like(self, video_id: str):
        try:
            url = f"https://graph.facebook.com/{self.GRAPH_VERSION}/{video_id}/likes"
            requests.post(url, data={"access_token": self.access_token}, timeout=15)
            print(f"[FACEBOOK] Auto-liked Reel {video_id}")
        except Exception as e:
            print(f"[FACEBOOK] Auto-like warning: {e}")

    def _auto_comment(self, video_id: str, comment_text: str):
        try:
            url = f"https://graph.facebook.com/{self.GRAPH_VERSION}/{video_id}/comments"
            requests.post(url, data={"message": comment_text, "access_token": self.access_token}, timeout=15)
            print(f"[FACEBOOK] Auto-commented: '{comment_text[:40]}...'")
        except Exception as e:
            print(f"[FACEBOOK] Auto-comment warning: {e}")
