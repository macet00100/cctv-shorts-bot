import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright

from src.config import BASE_DIR, OUTPUT_DIR, ASSETS_DIR

FOOTAGE_CACHE_DIR = ASSETS_DIR / "footage_cache"
FOOTAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MUSE_DATA_DIR = BASE_DIR / "muse_browser_data"

class MuseVideoEngine:
    """
    Automated Headless Video Generation Engine for Muse AI (Web App 31B Tokens).
    Uses a persistent browser session (Playwright) to interact with https://muse.ai,
    input prompts, wait for the AI video to render, and download the resulting MP4.
    """

    INCIDENT_PROMPT_PRESETS = {
        "CCTV": {
            "HEROIC_CLOSE_CALL": "Create a vertical 9:16 aspect ratio security camera video. Portrait orientation 9:16 framing. Storefront wide view on a sunny afternoon. A passerby notices an empty cardboard box tumbling off a cafe awning and smoothly catches it in mid-air right before it touches the ground. Impressive reflexes, wholesome street moment, realistic motion, authentic security camera angle with natural street audio. Vertical format 9:16.",
            "FUNNY_SLIP_TUMBLE": "Create a vertical 9:16 aspect ratio security camera viewpoint video, portrait orientation 9:16. Store lobby view. A person steps onto a shiny floor, does a comical harmless slip on both feet, regains balance against a wall and chuckles at their own clumsy stumble. Harmless funny slapstick moment, realistic physics with natural sound.",
            "TRAFFIC_NEAR_MISS": "Create a vertical 9:16 aspect ratio street corner security camera view, portrait orientation 9:16. A car driving down a quiet street stops smoothly as a large cardboard box rolls across the crosswalk, driver waves friendly hand, realistic street atmosphere with ambient engine and city audio.",
            "MIRACLE_CATCH_REFLEX": "Create a vertical 9:16 aspect ratio security camera viewpoint inside a store entrance, portrait orientation 9:16. A person fumbles their coffee cup, juggles it three times in mid-air, and catches it cleanly with both hands without spilling a drop. Customers nearby applaud, smooth authentic movement with store sounds.",
            "RUNAWAY_OBJECT_CHAOS": "Create a vertical 9:16 aspect ratio security camera view of a supermarket parking lot, portrait orientation 9:16. An empty shopping cart rolls slowly down a gentle slope on a windy day. A bystander gently stops it with their shoe and parks it safely, wholesome funny clip with natural audio."
        },
        "DASHCAM": {
            "HEROIC_CLOSE_CALL": "Create a vertical 9:16 aspect ratio car dashcam front windshield perspective video, portrait orientation 9:16. Suburban street driving. A colorful beach ball rolls across the asphalt, driver brakes smoothly to a stop letting the ball bounce onto the grass curb, authentic windshield camera view with realistic engine audio.",
            "TRAFFIC_NEAR_MISS": "Create a vertical 9:16 aspect ratio dashcam POV driving down a highway, portrait orientation 9:16. A large light empty cardboard box blows across the road on a breezy day. The driver maneuvers smoothly around it into the next lane, realistic vehicle movement and highway audio.",
            "FUNNY_SLIP_TUMBLE": "Create a vertical 9:16 aspect ratio car dashcam POV stopped at a red light, portrait orientation 9:16. Across the pedestrian crosswalk, a person in a funny inflatable dinosaur costume trips lightly over a curb, rolls playfully onto grass, stands up and takes a theatrical bow, driver perspective.",
            "MIRACLE_CATCH_REFLEX": "Create a vertical 9:16 aspect ratio dashcam POV waiting at an intersection, portrait orientation 9:16. A bicycle rider waiting ahead drops their water bottle, kicks it up with their heel, and catches it in hand cleanly, amazing reflex, casual street moment.",
            "RUNAWAY_OBJECT_CHAOS": "Create a vertical 9:16 aspect ratio dashcam POV driving down a quiet street, portrait orientation 9:16. A giant tumbleweed rolls across the road bouncing gently off the pavement, comical road incident with ambient car sound."
        },
        "DOORBELL_CAM": {
            "HEROIC_CLOSE_CALL": "Create a vertical 9:16 aspect ratio smart doorbell camera video looking at a front porch, portrait orientation 9:16. A delivery driver steps onto porch and a loose hat blows off their head in the wind. The homeowner opens the door and catches the hat mid-air with a smile, heartwarming friendly interaction, fisheye camera lens.",
            "FUNNY_SLIP_TUMBLE": "Create a vertical 9:16 aspect ratio smart doorbell camera POV looking at front porch steps, portrait orientation 9:16. A delivery courier walks up, feet slide gently forward on wooden deck, courier lands softly on bottom like a slide holding package up safely, courier laughs at the doorbell camera, funny harmless moment.",
            "TRAFFIC_NEAR_MISS": "Create a vertical 9:16 aspect ratio doorbell camera video overlooking a driveway, portrait orientation 9:16. A kid's toy tricycle slowly rolls down the driveway, a golden retriever dog runs and nudges it gently into the soft garden grass, adorable wholesome pet video.",
            "MIRACLE_CATCH_REFLEX": "Create a vertical 9:16 aspect ratio smart doorbell camera view, portrait orientation 9:16. A mail carrier tosses a newspaper toward the porch, homeowner opens door and catches it cleanly with one hand without looking, smooth reflex with front yard ambiance.",
            "RUNAWAY_OBJECT_CHAOS": "Create a vertical 9:16 aspect ratio doorbell camera on a windy afternoon, portrait orientation 9:16. A plastic trash bin is nudged by a gust of wind, rolls down driveway, and a friendly golden retriever catches up and playfully stops it, viral wholesome fail."
        },
        "BODYCAM": {
            "HEROIC_CLOSE_CALL": "Create a vertical 9:16 aspect ratio bicycle courier bodycam POV riding down a sunny city bike lane, portrait orientation 9:16. A pedestrian drops an envelope on the ground, the cyclist stops smoothly and hands it back, friendly city street ambiance.",
            "FUNNY_SLIP_TUMBLE": "Create a vertical 9:16 aspect ratio bodycam POV walking on a hiking trail, portrait orientation 9:16. Foot loses traction in light leaves, sliding down a gentle slope on feet like skiing, stopping safely against a wooden signpost, harmless funny stumble.",
            "TRAFFIC_NEAR_MISS": "Create a vertical 9:16 aspect ratio bicycle bodycam POV, portrait orientation 9:16. Car door opens slightly ahead in bike lane, cyclist smoothly rings bell and glides cleanly around the vehicle, authentic helmet camera with street sound.",
            "MIRACLE_CATCH_REFLEX": "Create a vertical 9:16 aspect ratio bodycam POV in a restaurant, portrait orientation 9:16. A tray of plastic cups tips off a table, wearer lunges forward and catches the edge of the tray with two hands, zero dropped cups, chef gives thumbs up, viral reflex save.",
            "RUNAWAY_OBJECT_CHAOS": "Create a vertical 9:16 aspect ratio patrol officer bodycam, portrait orientation 9:16. An empty runaway cart rolls down a gentle ramp in a park. Officer sprints and catches the handle cleanly, pedestrians smile, heartwarming incident."
        }
    }

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.user_data_dir = MUSE_DATA_DIR
        self.output_dir = OUTPUT_DIR

    def is_configured(self) -> bool:
        """Kiểm tra xem đã có phiên đăng nhập trong thư mục muse_browser_data chưa."""
        if not self.user_data_dir.exists():
            return False
        # Kiểm tra sự tồn tại của profile hoặc storage_state
        state_file = self.user_data_dir / "storage_state.json"
        return state_file.exists() or len(list(self.user_data_dir.glob("*"))) > 5

    def generate_video(self, scenario: Dict[str, Any], timeout_seconds: int = 360) -> Path:
        """
        Khởi động browser với profile đã đăng nhập, gửi prompt yêu cầu tạo video lên Muse AI,
        chờ Muse hoàn tất và tải video MP4 về máy.
        """
        if not self.is_configured():
            raise RuntimeError(
                "\n[MUSE AI ENGINE] ❌ Chưa tìm thấy phiên đăng nhập Muse AI!\n"
                "👉 Vui lòng chạy file 'DANG_NHAP_MUSE.bat' hoặc lệnh 'python login_muse.py' để đăng nhập trước 1 lần duy nhất."
            )

        camera_mode = scenario.get("camera_mode", "CCTV")
        incident_type = scenario.get("anomaly_type") or scenario.get("incident_type", "HEROIC_CLOSE_CALL")

        mode_presets = self.INCIDENT_PROMPT_PRESETS.get(camera_mode, self.INCIDENT_PROMPT_PRESETS["CCTV"])
        prompt = scenario.get("ai_video_prompt") or mode_presets.get(incident_type, mode_presets.get("HEROIC_CLOSE_CALL"))

        print(f"\n[MUSE AI ENGINE] 🤖 Khởi động Muse AI Web Automation (31B Token)...")
        print(f"📹 Chế độ Camera: {camera_mode} | Sự cố: {incident_type}")
        print(f"📝 Prompt: {prompt[:120]}...")

        timestamp = int(time.time())
        output_video_path = self.output_dir / f"muse_{camera_mode}_{timestamp}.mp4"

        captured_video_urls = []

        with sync_playwright() as p:
            launch_kwargs = {
                "user_data_dir": str(self.user_data_dir),
                "headless": self.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1280,800"
                ]
            }

            try:
                context = p.chromium.launch_persistent_context(channel="chrome", **launch_kwargs)
            except Exception:
                context = p.chromium.launch_persistent_context(**launch_kwargs)

            page = context.pages[0] if context.pages else context.new_page()

            # Bắt link tải video nếu server Muse phản hồi video stream/file
            def on_response(response):
                try:
                    content_type = response.headers.get("content-type", "").lower()
                    url = response.url.lower()
                    if ("video/mp4" in content_type or url.endswith(".mp4") or "fbcdn.net" in url and "mp4" in url) and response.status == 200:
                        if response.url not in captured_video_urls:
                            print(f"[MUSE AI] 🎯 Đã bắt được URL video stream: {response.url[:80]}...")
                            captured_video_urls.append(response.url)
                except Exception:
                    pass

            page.on("response", on_response)

            try:
                print("[MUSE AI] Đang truy cập https://muse.ai ...")
                page.goto("https://muse.ai", wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)

                # Tìm ô nhập liệu (chat input)
                # Muse Web sử dụng textarea, input, hoặc contenteditable div
                input_selectors = [
                    "textarea",
                    "div[contenteditable='true']",
                    "[placeholder*='Nhắn tin']",
                    "[placeholder*='nhắn tin']",
                    "[placeholder*='Message']",
                    "[placeholder*='message']",
                    "[placeholder*='Ask']",
                    "div[role='textbox']"
                ]

                input_elem = None
                for selector in input_selectors:
                    elem = page.locator(selector).first
                    if elem.count() > 0 and elem.is_visible():
                        input_elem = elem
                        print(f"[MUSE AI] Đã tìm thấy ô nhập liệu với selector: {selector}")
                        break

                if not input_elem:
                    # Nếu chưa thấy ngay, chụp ảnh màn hình để debug
                    debug_screenshot = self.output_dir / "debug_muse_not_found.png"
                    page.screenshot(path=str(debug_screenshot))
                    raise RuntimeError(f"Không tìm thấy ô nhập liệu trên https://muse.ai! Đã chụp ảnh debug: {debug_screenshot}")

                # Ghi nhận các video blob hiện có trước khi gửi câu lệnh
                existing_videos = page.locator("video").all()
                existing_blob_urls = set()
                for v in existing_videos:
                    s = v.get_attribute("src")
                    if s and s.startswith("blob:"):
                        existing_blob_urls.add(s)
                print(f"[MUSE AI] Số video blob hiện có trước khi gửi: {len(existing_blob_urls)}")

                # Nhập prompt tạo video vào ô chat
                input_elem.click()
                time.sleep(0.5)
                input_elem.fill(prompt)
                time.sleep(1)

                # Nhấn Enter để gửi
                print("[MUSE AI] 🚀 Đang gửi câu lệnh tạo video...")
                input_elem.press("Enter")

                # Chờ video render xong
                print(f"[MUSE AI] ⏳ Đang chờ Muse AI render video (tối đa {timeout_seconds}s)...")
                start_time = time.time()
                found_video = False

                js_code = """
                async (url) => {
                    const res = await fetch(url);
                    const blob = await res.blob();
                    if (blob.size < 1000000) return null; // Bỏ qua avatar animation (~300KB)
                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    });
                }
                """

                while (time.time() - start_time) < timeout_seconds:
                    time.sleep(5)
                    elapsed = int(time.time() - start_time)

                    # Cách 1: Bắt được link video từ network
                    if captured_video_urls:
                        target_url = captured_video_urls[-1]
                        print(f"[MUSE AI] 📥 Đang tải video từ URL bắt được...")
                        r = requests.get(target_url, stream=True, timeout=60)
                        if r.status_code == 200:
                            with open(output_video_path, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            if output_video_path.exists() and output_video_path.stat().st_size > 1000000:
                                print(f"[MUSE AI] ✅ Đã lưu video thành công: {output_video_path.name} ({output_video_path.stat().st_size / 1024 / 1024:.2f} MB)")
                                found_video = True
                                break

                    # Cách 2: Trích xuất blob video MỚI từ thẻ <video> trong DOM
                    video_elements = page.locator("video").all()
                    for v in video_elements:
                        src = v.get_attribute("src")
                        if src and src.startswith("blob:") and src not in existing_blob_urls:
                            try:
                                data_url = page.evaluate(js_code, src)
                                if data_url and data_url.startswith("data:video/mp4;base64,"):
                                    import base64
                                    header, encoded = data_url.split(",", 1)
                                    raw_bytes = base64.b64decode(encoded)
                                    if len(raw_bytes) > 1000000:
                                        with open(output_video_path, "wb") as f:
                                            f.write(raw_bytes)
                                        print(f"[MUSE AI] ✅ Đã trích xuất video AI thành công: {output_video_path.name} ({len(raw_bytes) / 1024 / 1024:.2f} MB)")
                                        found_video = True
                                        break
                            except Exception:
                                pass
                    if found_video:
                        break

                    # In tiến độ chờ
                    if elapsed % 15 == 0:
                        print(f"[MUSE AI] ... Đang xử lý ({elapsed}s / {timeout_seconds}s) ...")

                if not found_video:
                    debug_screenshot = self.output_dir / "debug_muse_timeout.png"
                    page.screenshot(path=str(debug_screenshot))
                    raise TimeoutError(f"Quá thời gian ({timeout_seconds}s) chờ Muse AI sinh video. Đã lưu ảnh debug: {debug_screenshot}")

            finally:
                context.close()

        return output_video_path
