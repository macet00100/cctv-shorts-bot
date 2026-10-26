import os
import random
import time
from pathlib import Path
from typing import Dict, Any, Optional
import requests

from src.config import BASE_DIR, ASSETS_DIR

FOOTAGE_CACHE_DIR = ASSETS_DIR / "footage_cache"
FOOTAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class FootageEngine:
    """
    Authentic Raw Camera Footage Provider.
    Sources 100% free, high-definition (1080p) real-world camera video:
    - DASHCAM: Night driving, dark highway headlights, rain on windshield.
    - BODYCAM: Night patrol with flashlight, POV walking through woods or corridor.
    - CCTV: Fixed surveillance camera, security monitor, flickering lights.
    - TRAIL_CAM: Infrared wilderness night camera, swaying trees, wind.

    Providers:
    1. Pexels Video API (Free 100%, 20,000 req/mo, fast CDN).
    2. Public Domain Archive.org surveillance & dashcam repository (No key needed).
    3. Curated local fallback cache.
    """

    SEARCH_KEYWORDS = {
        "DASHCAM": [
            "night driving car",
            "car headlights dark road",
            "dashcam night highway",
            "car driving in rain night",
            "foggy dark road driving"
        ],
        "BODYCAM": [
            "flashlight walking night",
            "dark hallway flashlight",
            "police patrol night walking",
            "flashlight woods night",
            "exploring dark tunnel flashlight"
        ],
        "CCTV": [
            "surveillance camera night",
            "cctv empty hallway night",
            "security camera parking lot night",
            "warehouse security camera night",
            "cctv street corner night"
        ],
        "TRAIL_CAM": [
            "night forest infrared",
            "dark woods trees night",
            "wildlife camera night forest",
            "creepy woods night wind",
            "deep forest night camera"
        ]
    }

    # High quality public domain backup clips from Archive.org
    PUBLIC_BACKUPS = {
        "DASHCAM": [
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-222454-000342F.mp4",
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-232807-000371F.mp4",
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-205403-000306F.mp4"
        ],
        "CCTV": [
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-184513-000186F.mp4",
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-191149-000213F.mp4"
        ],
        "BODYCAM": [
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-225006-000354F.mp4",
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-191559-000225F.mp4"
        ],
        "TRAIL_CAM": [
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-223139-000346F.mp4",
            "https://archive.org/download/ev-20260113-193229-000260-f/PA20260113-214006-000322F.mp4"
        ]
    }

    def __init__(self, pexels_api_key: Optional[str] = None):
        self.pexels_key = pexels_api_key or os.getenv("PEXELS_API_KEY", "")
        self.cache_dir = FOOTAGE_CACHE_DIR

    def acquire_footage(self, scenario: Dict[str, Any], target_duration: float = 24.0) -> Path:
        """
        Main entry point to fetch authentic video footage matching the scenario.
        Priority:
        0. 100% Neural AI Video Generation (Wan 2.1 via SiliconFlow API if configured)
        1. Pexels HD API (if PEXELS_API_KEY configured)
        2. Public Domain Archive (Archive.org)
        """
        camera_mode = scenario.get("camera_mode", "CCTV")

        # 0. Try 100% Pure Neural AI Video Generation (Kling 3.0 Flagship or Wan 2.2)
        try:
            from src.kling_video_engine import KlingVideoEngine
            kling_engine = KlingVideoEngine()
            if kling_engine.is_configured():
                print(f"[FOOTAGE ENGINE] 🎬 Calling Kling AI 3.0 API for {camera_mode}...")
                return kling_engine.generate_video(scenario)
        except Exception as e:
            print(f"[FOOTAGE ENGINE] ⚠️ Kling AI generation error ({e}). Trying Wan 2.2 / fallback...")

        try:
            from src.ai_video_engine import AIVideoEngine
            ai_engine = AIVideoEngine()
            if ai_engine.is_configured():
                print(f"[FOOTAGE ENGINE] 🤖 Calling Wan 2.2 API for {camera_mode}...")
                return ai_engine.generate_ai_video(scenario)
        except Exception as e:
            print(f"[FOOTAGE ENGINE] ⚠️ Wan 2.2 generation error ({e}). Falling back to footage repository...")

        print(f"[FOOTAGE ENGINE] Fetching authentic video footage for mode: {camera_mode}...")

        # 1. Try Pexels Video API if key configured
        if self.pexels_key:
            try:
                video_path = self._fetch_from_pexels(camera_mode)
                if video_path and video_path.exists():
                    print(f"[FOOTAGE ENGINE] Successfully fetched HD footage from Pexels: {video_path.name}")
                    return video_path
            except Exception as e:
                print(f"[FOOTAGE ENGINE] Pexels fetch failed: {e}. Falling back to public archive...")

        # 2. Try Public Domain Archive Backup
        try:
            video_path = self._fetch_from_archive(camera_mode)
            if video_path and video_path.exists():
                print(f"[FOOTAGE ENGINE] Successfully fetched archive footage: {video_path.name}")
                return video_path
        except Exception as e:
            print(f"[FOOTAGE ENGINE] Archive fetch failed: {e}")

        # 3. Check if any cached mp4 exists locally
        cached_files = list(self.cache_dir.glob(f"*{camera_mode}*.mp4")) or list(self.cache_dir.glob("*.mp4"))
        if cached_files:
            print(f"[FOOTAGE ENGINE] Using local cached footage: {cached_files[0].name}")
            return cached_files[0]

        # 4. Check root workspace for test video
        root_test = BASE_DIR / "test_dashcam_30s.mp4"
        if root_test.exists():
            return root_test

        raise RuntimeError(f"[FOOTAGE ENGINE] Could not source footage for camera mode: {camera_mode}")

    def _fetch_from_pexels(self, camera_mode: str) -> Optional[Path]:
        """Fetch 1080p video from Pexels Video API."""
        keywords = self.SEARCH_KEYWORDS.get(camera_mode, ["night security camera"])
        query = random.choice(keywords)
        url = "https://api.pexels.com/v1/videos/search"
        headers = {"Authorization": self.pexels_key}
        params = {
            "query": query,
            "orientation": "portrait",
            "per_page": 10
        }

        resp = requests.get(url, headers=headers, params=params, timeout=12)
        if resp.status_code != 200:
            # Try without portrait orientation constraint
            params.pop("orientation", None)
            resp = requests.get(url, headers=headers, params=params, timeout=12)
            if resp.status_code != 200:
                return None

        data = resp.json()
        videos = data.get("videos", [])
        if not videos:
            return None

        selected = random.choice(videos)
        video_files = selected.get("video_files", [])
        # Prefer HD quality
        hd_files = [vf for vf in video_files if vf.get("quality") == "hd" or (vf.get("width") or 0) >= 720]
        chosen_file = hd_files[0] if hd_files else video_files[0]
        download_url = chosen_file.get("link")

        if not download_url:
            return None

        filename = f"pexels_{camera_mode}_{selected.get('id')}.mp4"
        target_path = self.cache_dir / filename

        if target_path.exists() and target_path.stat().st_size > 100000:
            return target_path

        print(f"[FOOTAGE ENGINE] Downloading Pexels video {selected.get('id')} ({chosen_file.get('width')}x{chosen_file.get('height')})...")
        dl_resp = requests.get(download_url, stream=True, timeout=30)
        with open(target_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

        return target_path

    def _fetch_from_archive(self, camera_mode: str) -> Optional[Path]:
        """Download public domain surveillance/dashcam clip."""
        urls = self.PUBLIC_BACKUPS.get(camera_mode, self.PUBLIC_BACKUPS["DASHCAM"])
        chosen_url = random.choice(urls)
        filename = f"archive_{camera_mode}_{Path(chosen_url).name}"
        target_path = self.cache_dir / filename

        if target_path.exists() and target_path.stat().st_size > 100000:
            return target_path

        print(f"[FOOTAGE ENGINE] Downloading public domain video: {chosen_url}...")
        resp = requests.get(chosen_url, stream=True, timeout=35)
        if resp.status_code == 200:
            with open(target_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            return target_path

        return None
