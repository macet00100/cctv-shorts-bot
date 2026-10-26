import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.config import HISTORY_FILE

LOCATIONS_BY_MODE = {
    "CCTV": [
        "Times Square, New York",
        "Fifth Avenue, New York",
        "Camden High Street, London",
        "Oxford Circus, London",
        "Champs-Élysées, Paris",
        "Alexanderplatz, Berlin",
        "Dotonbori Canal, Osaka",
        "Akihabara Street, Tokyo",
        "Myeongdong Shopping Street, Seoul",
        "Bourke Street Mall, Melbourne",
        "Grand Central Terminal, New York",
        "Potsdamer Platz, Berlin",
        "SoHo Broadway, New York",
        "Piazza del Duomo, Milan",
        "Ramblas Promenade, Barcelona"
    ],
    "DASHCAM": [
        "Sunset Boulevard, Los Angeles",
        "Michigan Avenue, Chicago",
        "Pacific Coast Highway, Malibu",
        "Route 66 Historic Junction, Arizona",
        "Interstate 95 Mile 42, Florida",
        "Downtown Las Vegas Boulevard",
        "Autobahn A8 Junction, Munich",
        "Shuto Expressway Bay Route, Tokyo",
        "Santa Monica Boulevard, California",
        "West Loop Expressway, Chicago"
    ],
    "DOORBELL_CAM": [
        "Maplewood Suburban Porch, New Jersey",
        "Oakridge Front Steps, Seattle",
        "Highland Park Driveway, Texas",
        "Sunset Ridge Porch, Denver",
        "Pinecrest Suburban Cul-de-sac, Ohio",
        "Silver Lake Porch, Los Angeles",
        "Chestnut Hill Front Porch, Philadelphia",
        "Northbrook Residential Driveway, Illinois"
    ],
    "BODYCAM": [
        "Hongdae Walking Street, Seoul",
        "Pike Place Market, Seattle",
        "Montmartre Steps, Paris",
        "Fisherman's Wharf, San Francisco",
        "Brick Lane, London",
        "Faneuil Hall Marketplace, Boston",
        "South Beach Ocean Drive, Miami",
        "George Street Bike Lane, Sydney"
    ]
}

SAFE_INCIDENTS_BY_MODE = {
    "CCTV": [
        {
            "type": "MIRACLE_CATCH_REFLEX",
            "action": "A passerby notices a light empty cardboard box tumbling off a store awning and smoothly catches it in mid-air right before touching the ground. Incredible lightning reflex catch, crowd nearby turns in awe.",
            "hud": "REFLEX MOMENT - 1080P",
            "comment": "Bro has superhero reflexes! Would you have reacted fast enough to catch that? 👇"
        },
        {
            "type": "HEROIC_CLOSE_CALL",
            "action": "A rolling shopping cart picks up speed down a gentle sloped sidewalk toward a parked bicycle. A quick-thinking bystander dashes forward and traps the wheel with their shoe right in the nick of time.",
            "hud": "HEROIC SAVE - STREET CAM",
            "comment": "Not all heroes wear capes! Give this bystander a medal 👏"
        },
        {
            "type": "UNEXPLAINED_OBJECT_ANOMALY",
            "action": "A metal cafe chair on an empty outdoor patio slides smoothly across the pavement by itself for 3 feet with nobody around on a calm night, street light flickers once.",
            "hud": "NIGHT PATROL - UNEXPLAINED",
            "comment": "Wind or something unexplainable? Look closely at the chair movement! Tell us what you think 👇"
        }
    ],
    "DASHCAM": [
        {
            "type": "TRAFFIC_NEAR_MISS",
            "action": "A car drives down the road, driver spots a giant colorful inflatable ball rolling into the lane and brakes smoothly to a stop, tire smoke gently rises as the ball bounces safely onto the grass curb.",
            "hud": "ABS ACTIVE - EMERGENCY BRAKE",
            "comment": "Those brakes deserve a raise! Always keep 100% focus on the road 😳"
        },
        {
            "type": "RUNAWAY_OBJECT_DODGE",
            "action": "A light empty cardboard box blows across the windy avenue. The driver expertly steers smoothly into the adjacent lane dodging the debris cleanly without sudden jerk.",
            "hud": "HIGHWAY DASH - SMOOTH DODGE",
            "comment": "Clean recovery! Have you ever had debris fly toward your windshield like this?"
        }
    ],
    "DOORBELL_CAM": [
        {
            "type": "FUNNY_SLIP_TUMBLE",
            "action": "A friendly delivery person walking up porch steps does a comical cartoonish slip on their feet, regains balance against the wooden railing without dropping the parcel, and chuckles happily at the camera.",
            "hud": "SMART PORCH CAM - REC",
            "comment": "Slipped like in a cartoon but protected the package with his life! Give him a 5-star tip 😂"
        },
        {
            "type": "PET_HEROIC_SAVE",
            "action": "A plastic watering can blows down the front driveway in a wind gust, a playful golden retriever sprints and gently nudges it into the soft lawn grass, saving it from the road.",
            "hud": "FRONT DRIVEWAY - PET CAM",
            "comment": "Good dog! Protecting the yard from runaway objects 🐶❤️"
        }
    ],
    "BODYCAM": [
        {
            "type": "COURIER_REFLEX_CATCH",
            "action": "A bicycle courier glides down a crowded walkway, a shopper drops a paper envelope, courier swiftly catches it in one hand mid-air and hands it right back with a friendly wave.",
            "hud": "COURIER POV - QUICK REFLEX",
            "comment": "Hand-eye coordination on point! Pure muscle memory 🔥"
        }
    ]
}

CAMERA_MODES = ["CCTV", "DASHCAM", "DOORBELL_CAM", "BODYCAM"]

class AIStoryDirector:
    """
    100% Autonomous Procedural Director (Zero-Gemini Dependency).
    Generates rich, unique, viral surveillance scenarios with:
    - Title format: "[Tên địa điểm] - [DD/MM/YYYY]"
    - Zero duplication guarantee using history tracking
    - Meta Muse Policy-Safe prompts with native 9:16 vertical orientation
    """

    def __init__(self):
        self.history_file = HISTORY_FILE
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save history: {e}")

    def check_freshness(self, cooldown_minutes: int = 90) -> bool:
        """Kiểm tra thời gian đệm để không đăng bài dồn dập."""
        if not self.history:
            return True

        last_post = self.history[-1]
        completed_at_str = last_post.get("completed_at")
        if not completed_at_str:
            return True

        try:
            last_time = datetime.fromisoformat(completed_at_str.replace("Z", "+00:00"))
            now_time = datetime.now(timezone.utc)
            diff_minutes = (now_time - last_time).total_seconds() / 60.0

            if diff_minutes < cooldown_minutes:
                print(f"[FRESHNESS GUARD] Ca vừa đăng cách đây {diff_minutes:.1f} phút (< {cooldown_minutes} phút). Tự động bỏ qua ca này để bảo vệ kênh.")
                return False
            return True
        except Exception:
            return True

    def generate_scenario(self, override_mode: str = None) -> Dict[str, Any]:
        """
        Sinh kịch bản độc nhất vô nhị không trùng lặp,
        Tiêu đề: [Tên địa điểm] - [DD/MM/YYYY]
        """
        camera_mode = override_mode if override_mode in CAMERA_MODES else random.choice(CAMERA_MODES)

        # 1. Chọn địa điểm phù hợp theo loại camera và chống trùng lặp
        available_locs = LOCATIONS_BY_MODE.get(camera_mode, LOCATIONS_BY_MODE["CCTV"])
        recent_locations = {p.get("location_name") for p in self.history[-30:] if p.get("location_name")}
        filtered_locs = [loc for loc in available_locs if loc not in recent_locations]
        if not filtered_locs:
            filtered_locs = available_locs

        chosen_location = random.choice(filtered_locs)

        # 2. Chọn sự cố phù hợp với loại camera
        incidents_pool = SAFE_INCIDENTS_BY_MODE.get(camera_mode, SAFE_INCIDENTS_BY_MODE["CCTV"])
        incident = random.choice(incidents_pool)

        # 3. Định dạng ngày tháng năm & thời gian thực tế chính xác khi bắt đầu render
        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # 4. Tự động nhận diện Ngày / Đêm theo giờ render thực tế
        hour = now.hour
        is_night = (hour < 6 or hour >= 18)
        if is_night:
            period_desc = f"Nighttime scene in the dark hours at {now.strftime('%I:%M %p')}"
            lighting_desc = "Dark night atmosphere illuminated by glowing street lamps, neon lights and vehicle headlights, quiet dark street at night"
        else:
            period_desc = f"Daytime scene with bright natural daylight at {now.strftime('%I:%M %p')}"
            lighting_desc = "Bright clear natural daylight, vibrant daytime street atmosphere with realistic natural sunlight and shadows"

        # 5. Tiêu đề chuẩn theo yêu cầu: [Tên địa điểm] - [ngày/tháng/năm]
        case_title = f"{chosen_location} - {date_str}"
        case_number = f"{camera_mode[:3]}-{now.strftime('%m%d%H%M')}"

        # 6. Xây dựng Prompt tối ưu riêng cho Meta Muse Video (Chuẩn dọc 9:16 Native + Thời gian thực + Ánh sáng Ngày/Đêm)
        mode_descriptions = {
            "CCTV": "Create a vertical 9:16 aspect ratio photorealistic security camera viewpoint video, portrait orientation 9:16, high-angle street view",
            "DASHCAM": "Create a vertical 9:16 aspect ratio car dashcam front windshield perspective video, portrait orientation 9:16 driving along the road",
            "DOORBELL_CAM": "Create a vertical 9:16 aspect ratio smart front porch doorbell camera video, portrait orientation 9:16 with wide fisheye lens",
            "BODYCAM": "Create a vertical 9:16 aspect ratio first-person courier bodycam video, portrait orientation 9:16 moving forward"
        }
        camera_desc = mode_descriptions.get(camera_mode, "Create a vertical 9:16 aspect ratio security camera video")

        ai_prompt = (
            f"{camera_desc} at {chosen_location}. "
            f"Portrait orientation 9:16 framing. "
            f"{period_desc}. {lighting_desc}. "
            f"{incident['action']} "
            f"Authentic surveillance camera optics, realistic physics, smooth motion, natural ambient audio. "
            f"The on-screen camera timestamp displays exact real-time: {current_time_str}. "
            f"Vertical format 9:16."
        )

        scenario = {
            "case_title": case_title,
            "case_number": case_number,
            "location_name": chosen_location,
            "camera_mode": camera_mode,
            "anomaly_type": incident["type"],
            "exact_render_time": current_time_str,
            "is_night": is_night,
            "hud_text_location": f"{chosen_location.split(',')[0].upper()} - CAM 0{random.randint(1, 9)}",
            "simulated_hud_extra": incident["hud"],
            "ai_video_prompt": ai_prompt,
            "pinned_comment": incident["comment"],
            "youtube_tags": ["shorts", "cctv", "caughtoncamera", "dashcam", "viral", "closecall", "miracle", "securitycamera"],
            "core_tags": [camera_mode.lower(), incident["type"].lower(), chosen_location.split(',')[0].lower().replace(" ", "")]
        }

        print(f"\n[DIRECTOR 100% MUSE] 🎬 Kịch bản mới: {case_title}")
        print(f"📹 Camera: {camera_mode} | Địa điểm: {chosen_location}")
        print(f"🕒 Giờ render: {current_time_str} ({'BAN ĐÊM 🌙' if is_night else 'BAN NGÀY ☀️'})")
        print(f"📌 Sự cố: {incident['type']}")
        print(f"📝 Prompt: {ai_prompt[:130]}...\n")

        return scenario

    def record_completed_post(self, scenario: Dict[str, Any], yt_id: str = None, fb_id: str = None):
        """Ghi nhớ video đã xuất bản vào history để chống trùng lặp vĩnh viễn."""
        entry = {
            "id": scenario.get("case_number", f"cctv_{int(time.time())}"),
            "case_title": scenario.get("case_title"),
            "location_name": scenario.get("location_name"),
            "camera_mode": scenario.get("camera_mode"),
            "anomaly_type": scenario.get("anomaly_type"),
            "youtube_id": yt_id,
            "facebook_id": fb_id,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        self.history.append(entry)
        self._save_history()
        print(f"[HISTORY] ✅ Đã lưu lịch sử bài đăng: {entry['case_title']}")
