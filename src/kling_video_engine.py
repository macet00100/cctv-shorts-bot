import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import OUTPUT_DIR, ASSETS_DIR

FOOTAGE_CACHE_DIR = ASSETS_DIR / "footage_cache"
FOOTAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class KlingVideoEngine:
    """
    Official Kling AI API Video Engine (Kling 3.0 Flagship).
    Uses the user's official Kling Developer API key for 100% automated video generation.
    """

    SUBMIT_URL = "https://api.klingai.com/v1/videos/text2video"
    STATUS_URL_TEMPLATE = "https://api.klingai.com/v1/videos/text2video/{task_id}"

    INCIDENT_PROMPT_PRESETS = {
        "CCTV": {
            "HEROIC_CLOSE_CALL": "CCTV surveillance camera footage, wide-angle street view outside an apartment building sidewalk. An unsuspecting woman in casual clothes walks along the pavement. Suddenly, a ceramic flower pot plummets from high above. A quick-thinking bystander man lunges and pushes her safely onto the pavement in the nick of time. The heavy flowerpot smashes violently on the concrete pavement exactly where she walked, exploding into broken ceramic shards and dark potting soil. Bystanders turn around in shock, realistic physics, authentic surveillance camera angle, raw footage, photorealistic, no CGI.",
            "FUNNY_SLIP_TUMBLE": "CCTV camera wide view of a clean convenience store entrance or lobby. A person walks in, steps onto freshly mopped floor, legs slide out like a cartoon slip, safely lands on their backside, sits there stunned for a second, then chuckles and picks up their dropped hat, harmless funny fail, realistic physics.",
            "TRAFFIC_NEAR_MISS": "CCTV camera view of a street intersection. A pedestrian steps into the crosswalk, a turning vehicle slams on the brakes with smoking tires, stopping mere inches from their knees, driver and pedestrian exchange stunned apologies, dramatic close call, raw camera footage.",
            "MIRACLE_CATCH_REFLEX": "CCTV security camera view inside a store. A stack of boxed items or bottles begins tumbling off a high shelf. A quick-reflex worker dives forward and catches the falling items in mid-air in an impossible heroic reflex, customers stare in awe, authentic security video.",
            "RUNAWAY_OBJECT_CHAOS": "CCTV street camera view outside a supermarket. A rogue runaway shopping cart rolls rapidly down the sloped pavement. A heroic passerby dashes forward and traps the cart with their foot right before it hits a parked car, safe harmless funny incident, raw surveillance footage."
        },
        "DASHCAM": {
            "HEROIC_CLOSE_CALL": "Car dashcam front windshield POV driving along a suburban street. A loose bicycle or child's ball rolls into the road, a mother sprints and pulls her toddler safely back to the sidewalk just as the car comes to a screeching halt, heart-stopping close call, realistic emergency braking, high resolution.",
            "TRAFFIC_NEAR_MISS": "Dashcam POV from front windshield of car driving on highway at daytime. Suddenly a huge cardboard box or light mattress flies off a pickup truck ahead. The driver expertly swerves into the shoulder lane dodging the debris cleanly without collision, high adrenaline near miss, authentic windshield camera view.",
            "FUNNY_SLIP_TUMBLE": "Car dashcam stopped at a red light. Across the pedestrian crossing, a costumed mascot trips over a curb, rolls harmlessly onto grass, stands up and takes a theatrical bow, amusing street moment, driver POV.",
            "MIRACLE_CATCH_REFLEX": "Dashcam POV of vehicle waiting at intersection. A cyclist ahead drops their phone, juggles it three times with feet and hands, and catches it safely without dropping it on the road, amazing reflex, street comedy.",
            "RUNAWAY_OBJECT_CHAOS": "Dashcam POV driving down a quiet street. A giant inflated beach ball or rogue tumbleweed rolls right across the road bouncing off the hood softly, comical harmless road incident."
        },
        "DOORBELL_CAM": {
            "HEROIC_CLOSE_CALL": "Smart doorbell camera looking at a front porch. A delivery driver places a package by the door. Suddenly a heavy tree branch cracks from above. The homeowner swings the door open and pulls the driver inside just as the branch crashes onto the porch railing, miraculous save, authentic fisheye lens.",
            "FUNNY_SLIP_TUMBLE": "Smart doorbell camera POV looking at front porch steps covered in light winter ice. A delivery courier walks up, feet slip forward, courier slides down three wooden steps on their bottom like a slide, package held safely in hand, courier laughs at the doorbell camera, harmless funny fail, genuine Ring camera look.",
            "TRAFFIC_NEAR_MISS": "Doorbell camera overlooking driveway. A driver forgets the handbrake and car rolls slowly backwards toward the street. The driver dashes out, leaps into the open door, and pulls the emergency handbrake 1 foot before hitting the mailbox, close call hero save.",
            "MIRACLE_CATCH_REFLEX": "Smart doorbell camera view. A mail carrier tosses a newspaper toward the porch, homeowner opens door and catches it cleanly with one hand without looking, smooth reflex, authentic front porch video.",
            "RUNAWAY_OBJECT_CHAOS": "Doorbell camera on windy afternoon. A plastic trash bin is caught by a wind gust, rolls down the driveway, and a cute golden retriever chases it down and knocks it into the grass, wholesome viral fail."
        },
        "BODYCAM": {
            "HEROIC_CLOSE_CALL": "Bicycle courier bodycam POV riding down busy city street. Ahead, a distracted pedestrian is about to step backward into traffic. The courier reaches out and firmly pulls the pedestrian's backpack, saving them from the road, first-person perspective, authentic street ambiance.",
            "FUNNY_SLIP_TUMBLE": "Bodycam POV of a park ranger or delivery person walking on a muddy trail, foot loses traction, sliding down a gentle muddy slope on feet like skiing, stopping safely against a wooden signpost, harmless funny stumble.",
            "TRAFFIC_NEAR_MISS": "Bicycle bodycam POV. Car door opens suddenly in bike lane, courier expertly bunny-hops or swerves 2 inches around the door, heart-pounding close call with clean recovery, authentic helmet camera.",
            "MIRACLE_CATCH_REFLEX": "Bodycam POV in a restaurant or kitchen. A heavy tray of dishes tips off a table, wearer lunges forward and catches the edge of the tray with two hands, zero broken plates, chef gives thumbs up, viral reflex save.",
            "RUNAWAY_OBJECT_CHAOS": "Patrol officer bodycam. A runaway stroller with no baby rolls down a ramp. Officer sprints and catches the handle cleanly, grocery bags saved, pedestrians clap, heartwarming incident."
        }
    }

    NEGATIVE_PROMPT = "fatal accident, blood, gore, severe injury, death, violence, cartoon, 3D CGI render, glossy, anime, distorted morphing bodies, watermark, logo"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("KLING_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("api-key-kling-"))

    def generate_video(self, scenario: Dict[str, Any], timeout_seconds: int = 400) -> Path:
        """
        Submits prompt to Kling AI 3.0 API, polls for completion,
        and downloads the 100% AI-generated video file.
        """
        if not self.is_configured():
            raise RuntimeError(
                "[KLING VIDEO ENGINE] KLING_API_KEY is not configured! "
                "Please add KLING_API_KEY to your .env file."
            )

        camera_mode = scenario.get("camera_mode", "CCTV")
        incident_type = scenario.get("anomaly_type") or scenario.get("incident_type", "HEROIC_CLOSE_CALL")

        mode_presets = self.INCIDENT_PROMPT_PRESETS.get(camera_mode, self.INCIDENT_PROMPT_PRESETS["CCTV"])
        prompt = scenario.get("ai_video_prompt") or mode_presets.get(incident_type, mode_presets.get("HEROIC_CLOSE_CALL"))

        print(f"\n[KLING AI ENGINE] 🎬 Submitting 100% AI Video generation task to Kling 3.0...")
        print(f"📹 Mode: {camera_mode} | Incident: {incident_type}")
        print(f"📝 Prompt: {prompt[:120]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model_name": "kling-v3",
            "prompt": prompt,
            "negative_prompt": self.NEGATIVE_PROMPT,
            "duration": "5",
            "aspect_ratio": "9:16",
            "mode": "std"
        }

        # 1. Submit text2video task
        resp = requests.post(self.SUBMIT_URL, json=payload, headers=headers, timeout=20)
        res_data = resp.json()
        if res_data.get("code") != 0:
            raise RuntimeError(f"Kling API Error ({res_data.get('code')}): {res_data.get('message')}")

        task_id = res_data.get("data", {}).get("task_id") or res_data.get("data", {}).get("id")
        if not task_id:
            raise RuntimeError(f"No task_id returned from Kling API: {res_data}")

        print(f"[KLING AI ENGINE] Task accepted! Task ID: {task_id}")

        # 2. Poll for completion
        status_url = self.STATUS_URL_TEMPLATE.format(task_id=task_id)
        start_time = time.time()
        video_download_url = None

        while time.time() - start_time < timeout_seconds:
            time.sleep(8)
            try:
                poll_resp = requests.get(status_url, headers=headers, timeout=15)
                poll_data = poll_resp.json()
                task_status = poll_data.get("data", {}).get("task_status")
                print(f"[KLING AI ENGINE] Status: {task_status} ({int(time.time() - start_time)}s elapsed)...")

                if task_status == "succeed":
                    works = poll_data.get("data", {}).get("task_result", {}).get("videos", [])
                    if works:
                        video_download_url = works[0].get("url")
                        print(f"[KLING AI ENGINE] Video render complete! URL: {video_download_url[:60]}...")
                        break
                elif task_status == "failed":
                    msg = poll_data.get("data", {}).get("task_status_msg", "Unknown error")
                    raise RuntimeError(f"Kling video generation failed: {msg}")

            except Exception as e:
                print(f"[KLING AI ENGINE] Polling warning: {e}")

        if not video_download_url:
            raise TimeoutError(f"Kling video generation timed out after {timeout_seconds} seconds.")

        # 3. Download generated MP4 video
        target_path = FOOTAGE_CACHE_DIR / f"ai_kling_{camera_mode}_{int(time.time())}.mp4"
        print(f"[KLING AI ENGINE] Downloading completed AI video file...")
        dl_resp = requests.get(video_download_url, stream=True, timeout=45)
        with open(target_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

        print(f"✅ [KLING AI ENGINE] 100% AI Incident Video Ready: {target_path.name} ({target_path.stat().st_size} bytes)")
        return target_path
