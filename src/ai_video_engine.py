import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import OUTPUT_DIR, ASSETS_DIR

FOOTAGE_CACHE_DIR = ASSETS_DIR / "footage_cache"
FOOTAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class AIVideoEngine:
    """
    100% Headless Automated AI Video Generation Engine (Wan 2.2 14B).
    Generates real-life shocking close calls, heroic saves & funny mishaps:
    - CCTV: Falling flowerpot heroic save, falling sign, runaway cart.
    - DASHCAM: Emergency brake close call, narrow miss, runaway tire.
    - DOORBELL_CAM: Delivery courier comical slip on ice, package catch.
    - BODYCAM: Heroic catch, reflex dodge, quick-thinking civilian save.
    100% Non-Violent, zero gore, family-friendly, viral engagement.
    """

    SILICONFLOW_SUBMIT_URL = "https://api.siliconflow.com/v1/video/submit"
    SILICONFLOW_STATUS_URL = "https://api.siliconflow.com/v1/video/status"

    INCIDENT_PROMPT_PRESETS = {
        "CCTV": {
            "HEROIC_CLOSE_CALL": "CCTV surveillance camera footage, wide-angle high street view outside a building sidewalk. A woman in casual clothes walks along the pavement. Suddenly, a ceramic flowerpot drops from high above. A quick-thinking bystander man lunges and pushes her safely onto the pavement in the nick of time. The heavy flowerpot smashes violently on the concrete pavement exactly where she walked, exploding into broken ceramic shards and dark potting soil. Bystanders turn around in shock, realistic physics, authentic surveillance camera angle, raw footage, photorealistic, no CGI.",
            "FUNNY_SLIP_TUMBLE": "CCTV camera wide view of a clean convenience store entrance or lobby. A person walks in, steps onto freshly mopped floor, legs slide out like a cartoon slip, safely lands on their backside, sits there stunned for a second, then chuckles and picks up their dropped hat, harmless funny fail, realistic physics.",
            "TRAFFIC_NEAR_MISS": "CCTV camera view of a street intersection. A pedestrian steps into the crosswalk, a turning vehicle slams on the brakes with smoking tires, stopping mere inches from their knees, driver and pedestrian exchange stunned apologies, dramatic close call, raw camera footage.",
            "MIRACLE_CATCH_REFLEX": "CCTV security camera view inside a store. A stack of boxed items or bottles begins tumbling off a high shelf. A quick-reflex worker dives forward and catches the falling items in mid-air in an impossible heroic reflex, customers stare in awe, authentic security video.",
            "RUNAWAY_OBJECT_CHAOS": "CCTV street camera view outside a supermarket. A rogue runaway shopping cart rolls rapidly down the sloped pavement. A heroic passerby dashes forward and traps the cart with their foot right before it hits a parked car, safe harmless funny incident, raw surveillance footage."
        },
        "DASHCAM": {
            "HEROIC_CLOSE_CALL": "Car dashcam front windshield POV driving along a suburban street. A loose bicycle or child's ball rolls into the road, a mother sprints and pulls her toddler safely back to the sidewalk just as the car comes to a screeching halt, heart-stopping close call, realistic emergency braking, high resolution.",
            "TRAFFIC_NEAR_MISS": "Dashcam POV from front windshield of car driving on highway at daytime. Suddenly a huge cardboard box or light mattress flies off a pickup truck ahead. The driver expertly swerves into the shoulder lane dodging the debris cleanly without collision, high adrenaline near miss, authentic windshield camera view.",
            "FUNNY_SLIP_TUMBLE": "Car dashcam stopped at a red light. Across the pedestrian crossing, a costumed mascot or funny walker trips over a curb, rolls harmlessly onto a patch of grass, stands up and takes a theatrical bow, amusing street moment, driver POV.",
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
            "RUNAWAY_OBJECT_CHAOS": "Patrol officer bodycam. A runaway stroller with no baby (just groceries) rolls down a ramp. Officer sprints and catches the handle cleanly, grocery bags saved, pedestrians clap, heartwarming incident."
        }
    }

    NEGATIVE_PROMPT = "fatal accident, blood, gore, broken bones, severe injury, death, violence, fighting, weapons, cartoon, 3D CGI render, glossy, anime, distorted morphing bodies, watermark, logo"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY") or os.getenv("WAN_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def generate_ai_video(self, scenario: Dict[str, Any], timeout_seconds: int = 400) -> Path:
        """
        Submits incident prompt to Wan 2.2 via SiliconFlow, polls for completion,
        and downloads the 100% AI-generated video file.
        """
        if not self.is_configured():
            raise RuntimeError(
                "[AI VIDEO ENGINE] SILICONFLOW_API_KEY is not configured! "
                "Please add SILICONFLOW_API_KEY to your .env file."
            )

        camera_mode = scenario.get("camera_mode", "CCTV")
        incident_type = scenario.get("anomaly_type") or scenario.get("incident_type", "HEROIC_CLOSE_CALL")

        # Select prompt preset matching mode & incident
        mode_presets = self.INCIDENT_PROMPT_PRESETS.get(camera_mode, self.INCIDENT_PROMPT_PRESETS["CCTV"])
        prompt = mode_presets.get(incident_type, mode_presets.get("HEROIC_CLOSE_CALL"))

        # If custom case prompt provided in scenario
        if scenario.get("ai_video_prompt"):
            prompt = scenario["ai_video_prompt"]

        print(f"\n[AI VIDEO ENGINE] 🎬 Submitting 100% AI Incident Video to Wan 2.2...")
        print(f"📹 Mode: {camera_mode} | Type: {incident_type}")
        print(f"📝 Prompt: {prompt[:120]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Wan 2.2 14B model identifier
        payload = {
            "model": "Wan-AI/Wan2.2-T2V-A14B",
            "prompt": prompt,
            "image_size": "720x1280",  # Native vertical 9:16 Shorts/Reels!
            "negative_prompt": self.NEGATIVE_PROMPT
        }

        # 1. Submit asynchronous video generation task
        try:
            resp = requests.post(self.SILICONFLOW_SUBMIT_URL, json=payload, headers=headers, timeout=20)
            if resp.status_code != 200:
                raise RuntimeError(f"Submit failed ({resp.status_code}): {resp.text}")

            result = resp.json()
            request_id = result.get("requestId") or result.get("id")
            if not request_id:
                raise RuntimeError(f"No requestId returned from API: {result}")

            print(f"[AI VIDEO ENGINE] Task accepted! Request ID: {request_id}")

        except Exception as e:
            raise RuntimeError(f"Failed to submit task to SiliconFlow API: {e}")

        # 2. Poll for completion
        start_time = time.time()
        status_url = self.SILICONFLOW_STATUS_URL
        video_download_url = None

        while time.time() - start_time < timeout_seconds:
            time.sleep(8)
            try:
                status_resp = requests.post(
                    status_url,
                    json={"requestId": request_id},
                    headers=headers,
                    timeout=15
                )

                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    status = status_data.get("status") or status_data.get("state")
                    results = status_data.get("results")
                    print(f"[AI VIDEO ENGINE] Status: {status} ({int(time.time() - start_time)}s elapsed)...")

                    # Check if results already present (even if status says InQueue/Succeed)
                    if isinstance(results, dict) and "videos" in results and results["videos"]:
                        video_download_url = results["videos"][0].get("url")
                        if video_download_url:
                            print(f"[AI VIDEO ENGINE] Video render complete! URL: {video_download_url[:60]}...")
                            break

                    if status in ["Succeed", "SUCCESS", "completed"]:
                        if not video_download_url and isinstance(results, dict) and "videos" in results:
                            video_download_url = results["videos"][0].get("url")
                        elif not video_download_url and "output" in status_data:
                            video_download_url = status_data["output"].get("url") or status_data.get("output")

                        if video_download_url:
                            print(f"[AI VIDEO ENGINE] Video render complete! URL: {video_download_url[:60]}...")
                            break

                    elif status in ["Failed", "FAILED", "error"]:
                        raise RuntimeError(f"Video generation task failed: {status_data}")

            except Exception as e:
                print(f"[AI VIDEO ENGINE] Polling warning: {e}")

        if not video_download_url:
            raise TimeoutError(f"Video generation timed out after {timeout_seconds} seconds.")

        # 3. Download generated MP4 video
        target_path = FOOTAGE_CACHE_DIR / f"ai_wan22_{camera_mode}_{int(time.time())}.mp4"
        print(f"[AI VIDEO ENGINE] Downloading completed AI video file...")
        dl_resp = requests.get(video_download_url, stream=True, timeout=45)
        with open(target_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

        print(f"✅ [AI VIDEO ENGINE] 100% AI Incident Video Ready: {target_path.name} ({target_path.stat().st_size} bytes)")
        return target_path
