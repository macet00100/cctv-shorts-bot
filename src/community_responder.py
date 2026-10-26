import json
import time
from typing import List, Dict, Any

try:
    from google import genai
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config import (
    GEMINI_API_KEY,
    HISTORY_FILE,
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    YOUTUBE_REFRESH_TOKEN,
    FB_PAGE_ID,
    FB_PAGE_ACCESS_TOKEN
)

class AICommunityEngagementBot:
    """
    AI Community Engagement & Comment Responder.
    Acts as a Digital Forensics & Surveillance Analyst to intelligently reply
    to audience theories, sparking viral debate and boosting retention metrics.
    """

    def __init__(self):
        self.gemini_key = GEMINI_API_KEY
        self.client = None
        if self.gemini_key:
            if HAS_NEW_GENAI:
                self.client = genai.Client(api_key=self.gemini_key)
            elif HAS_LEGACY_GENAI:
                legacy_genai.configure(api_key=self.gemini_key)

    def run_engagement_cycle(self):
        print("[COMMUNITY BOT] Starting comment scanning and reply cycle...")
        history = self._load_recent_posts(limit=5)
        if not history:
            print("[COMMUNITY BOT] No recent posts found in history.")
            return

        for post in history:
            yt_id = post.get("youtube_id")
            fb_id = post.get("facebook_id")

            if yt_id and YOUTUBE_REFRESH_TOKEN:
                self._process_youtube_comments(yt_id, post)

            if fb_id and FB_PAGE_ACCESS_TOKEN:
                self._process_facebook_comments(fb_id, post)

        print("[COMMUNITY BOT] Engagement cycle complete.")

    def _load_recent_posts(self, limit: int = 5) -> List[Dict[str, Any]]:
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data[-limit:] if isinstance(data, list) else []
        except Exception:
            return []

    def _generate_ai_reply(self, user_comment: str, post_info: Dict[str, Any]) -> str:
        prompt = f"""
You are the Lead Digital Forensics Analyst for an archival surveillance channel.
A viewer left this comment on our video "{post_info.get('case_title', 'CCTV Footage')}":
Viewer comment: "{user_comment}"

Task: Write a short, highly intriguing reply (1-2 sentences maximum, under 35 words).
Rules:
- Speak as a calm, analytical digital investigator.
- Never directly confirm it's 100% supernatural, but point out a subtle perplexing anomaly or question their theory.
- Keep the debate alive and provoke them or others to reply again.
- Use English.
"""
        try:
            target_model = "gemini-3.8-flash"
            if HAS_NEW_GENAI and self.client:
                try:
                    res = self.client.models.generate_content(
                        model=target_model,
                        contents=prompt
                    )
                except Exception:
                    res = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                return res.text.strip().replace('"', '')
            elif HAS_LEGACY_GENAI:
                try:
                    model = legacy_genai.GenerativeModel(target_model)
                    res = model.generate_content(prompt)
                except Exception:
                    model = legacy_genai.GenerativeModel("gemini-2.5-flash")
                    res = model.generate_content(prompt)
                return res.text.strip().replace('"', '')
            else:
                return "Good catch. But look at the shadow trajectory at that exact second... What explains that?"
        except Exception as e:
            print(f"[COMMUNITY BOT] Gemini generation error: {e}")
            return "Good catch. But look at the shadow trajectory at that exact second... What explains that?"

    def _process_youtube_comments(self, video_id: str, post_info: Dict[str, Any]):
        try:
            creds = Credentials(
                None,
                refresh_token=YOUTUBE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=YOUTUBE_CLIENT_ID,
                client_secret=YOUTUBE_CLIENT_SECRET,
                scopes=["https://www.googleapis.com/auth/youtube.force-ssl"]
            )
            youtube = build("youtube", "v3", credentials=creds)

            # Get comments
            threads = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                order="time",
                maxResults=10
            ).execute()

            for item in threads.get("items", []):
                snippet = item["snippet"]
                top_comment = snippet["topLevelComment"]["snippet"]
                comment_id = item["snippet"]["topLevelComment"]["id"]
                comment_text = top_comment["textDisplay"]
                total_reply_count = snippet.get("totalReplyCount", 0)

                # Skip if already replied or if it's our own comment
                if total_reply_count > 0:
                    continue

                print(f"[COMMUNITY BOT] YouTube comment found: '{comment_text[:40]}...'")
                ai_reply = self._generate_ai_reply(comment_text, post_info)

                # Post reply
                youtube.comments().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "parentId": comment_id,
                            "textOriginal": ai_reply
                        }
                    }
                ).execute()

                print(f"[COMMUNITY BOT] Replied on YouTube: '{ai_reply}'")
                time.sleep(2)

        except Exception as e:
            print(f"[COMMUNITY BOT] YouTube engagement error for {video_id}: {e}")

    def _process_facebook_comments(self, video_id: str, post_info: Dict[str, Any]):
        try:
            url = f"https://graph.facebook.com/v19.0/{video_id}/comments"
            params = {"access_token": FB_PAGE_ACCESS_TOKEN, "limit": 10}
            resp = requests.get(url, params=params, timeout=20)
            data = resp.json()

            for c in data.get("data", []):
                comment_id = c.get("id")
                message = c.get("message", "")
                if not message:
                    continue

                # Check if we already replied to this comment
                sub_resp = requests.get(
                    f"https://graph.facebook.com/v19.0/{comment_id}/comments",
                    params={"access_token": FB_PAGE_ACCESS_TOKEN},
                    timeout=15
                )
                if len(sub_resp.json().get("data", [])) > 0:
                    continue

                ai_reply = self._generate_ai_reply(message, post_info)
                reply_url = f"https://graph.facebook.com/v19.0/{comment_id}/comments"
                requests.post(
                    reply_url,
                    data={"message": ai_reply, "access_token": FB_PAGE_ACCESS_TOKEN},
                    timeout=15
                )
                print(f"[COMMUNITY BOT] Replied on Facebook: '{ai_reply}'")
                time.sleep(2)

        except Exception as e:
            print(f"[COMMUNITY BOT] Facebook engagement error for {video_id}: {e}")

if __name__ == "__main__":
    bot = AICommunityEngagementBot()
    bot.run_engagement_cycle()
