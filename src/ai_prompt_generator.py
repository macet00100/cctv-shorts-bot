import argparse
import sys
import os
import json
from pathlib import Path

# Safe Unicode output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.config import BASE_DIR, OUTPUT_DIR
from src.ai_story_director import AIStoryDirector
from src.image_generator import FoundFootageImageGenerator

TASK_DIR = BASE_DIR / "ai_tasks"
TASK_DIR.mkdir(parents=True, exist_ok=True)

class AIPromptDirector:
    """
    Directs and prepares hyper-optimized generation packages for:
    - Kling AI (klingai.com)
    - Hailuo AI (hailuoai.video / minimax.io)
    - Luma Dream Machine (lumalabs.ai)

    Generates:
    1. Photorealistic Starting Frame (.jpg) via FLUX.
    2. Exact copy-paste Prompt & Negative Prompt for Image-to-Video / Text-to-Video.
    3. Motion & Camera guidance settings.
    """

    PROMPT_TEMPLATES = {
        "CCTV": {
            "t2v_prompt": "CCTV security surveillance camera POV, high angle corner mount, wide angle fisheye lens, authentic 2012 DVR timestamp recording, dimly lit abandoned {location_desc}. At second 2, a subtle eerie tall silhouette emerges slowly from the shadows near the far doorway, moving with unnatural stiff cadence across the corridor, flickering overhead fluorescent light, photorealistic, raw found footage, 50/50 realism, uncanny valley, grain, high ISO noise, no CGI.",
            "i2v_prompt": "The camera feed flickers slightly. The dark shadowy figure at the far end of the hallway slowly shifts position, taking two slow deliberate unnatural steps forward before pausing in the dim light, authentic surveillance camera grain, micro-jitter.",
            "camera_movement": "Fixed camera with slight electrical sensor buzz and minor micro-shake.",
            "motion_score": "5 / 10 (Realistic, not frantic)"
        },
        "BODYCAM": {
            "t2v_prompt": "Police officer bodycam POV footage, Axon body camera mounted on tactical vest, running footsteps and tactical breathing, dark {location_desc} illuminated only by high-intensity tactical flashlight beam. As the flashlight sweeps across the corner at second 3, an ambiguous pale distorted silhouette is caught for 2 seconds behind the frame before ducking away, realistic physical motion, camera bobbing, lens flare, authentic lens dust, raw footage.",
            "i2v_prompt": "First-person POV walking forward with tactical flashlight beam bouncing on the ground. The flashlight sweeps toward the dark opening where a tall uncanny shape briefly ducks back into the pitch black shadow.",
            "camera_movement": "First-person walking bob, natural tactical handheld sway.",
            "motion_score": "6 / 10"
        },
        "DASHCAM": {
            "t2v_prompt": "Dashcam POV footage from front windshield of a car driving along a dark, foggy {location_desc} at night. High beam headlights illuminating wet asphalt and reflective signs. At second 3, the headlights illuminate an ambiguous tall shadowy figure standing motionlessly on the shoulder near the treeline before the car passes it, realistic vehicle speed motion, windshield wiper sweep, photorealistic, uncanny, eerie found footage.",
            "i2v_prompt": "The car continues driving down the dark night road, headlights cutting through the fog. The dark ambiguous silhouette on the roadside comes into sharper focus before slipping into the darkness behind.",
            "camera_movement": "Forward moving vehicle POV with realistic road vibration.",
            "motion_score": "6 / 10"
        },
        "TRAIL_CAM": {
            "t2v_prompt": "Trail camera infrared night vision footage, monochrome green/black IR illumination, static hunting camera mounted on a pine tree in deep {location_desc}. Motion sensor triggered. Wind gently swaying branches. Between the dense trees at second 2, two faint reflective eyes appear, blink once, and an indistinct bipedal creature moves slowly behind a thick trunk, hyper-realistic, authentic wildlife camera, creepy 50/50 found footage.",
            "i2v_prompt": "Infrared night camera footage. The wind blows through the trees. In the dark background, the reflective eyes blink and the shadowy shape shifts behind the thick tree trunk.",
            "camera_movement": "Completely static trailcam trap, natural wind rustle.",
            "motion_score": "4 / 10"
        }
    }

    NEGATIVE_PROMPT = "cartoon, 3D animation, CGI, glossy, video game graphics, anime, bright vibrant colors, happy, cheerful, fake movie set, watermark, text banner, logo, oversaturated, morphing melting faces"

    def __init__(self):
        self.director = AIStoryDirector()
        self.img_gen = FoundFootageImageGenerator()

    def prepare_task(self, mode: str = None) -> dict:
        scenario = self.director.generate_scenario(override_mode=mode)
        camera_mode = scenario.get("camera_mode", "CCTV")
        location_type = scenario.get("location_type", "GAS_STATION_STORE").replace("_", " ").lower()

        # 1. Generate Starting Frame with FLUX
        print(f"\n[AI PROMPT DIRECTOR] Generating high-resolution Starting Frame for {camera_mode}...")
        start_frame_path = self.img_gen.generate(scenario)
        
        # Copy to task folder
        task_id = f"task_{camera_mode}_{int(start_frame_path.stem.split('_')[-1])}"
        target_frame = TASK_DIR / f"{task_id}_start_frame.jpg"
        target_frame.write_bytes(start_frame_path.read_bytes())

        # 2. Build Prompts
        tmpl = self.PROMPT_TEMPLATES.get(camera_mode, self.PROMPT_TEMPLATES["CCTV"])
        t2v_prompt = tmpl["t2v_prompt"].format(location_desc=location_type)
        i2v_prompt = tmpl["i2v_prompt"]

        task_data = {
            "task_id": task_id,
            "camera_mode": camera_mode,
            "location_type": scenario.get("location_type"),
            "anomaly_type": scenario.get("anomaly_type"),
            "case_title": scenario.get("case_title"),
            "pinned_comment": scenario.get("pinned_comment"),
            "youtube_tags": scenario.get("youtube_tags"),
            "start_frame_path": str(target_frame),
            "kling_image_to_video_prompt": i2v_prompt,
            "kling_text_to_video_prompt": t2v_prompt,
            "negative_prompt": self.NEGATIVE_PROMPT,
            "recommended_motion": tmpl["motion_score"],
            "recommended_camera": tmpl["camera_movement"]
        }

        # Save task JSON
        json_path = TASK_DIR / f"{task_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)

        return task_data

def main():
    parser = argparse.ArgumentParser(description="AI Video Prompt & Asset Director for Kling / Hailuo")
    parser.add_argument("--mode", type=str, choices=["CCTV", "BODYCAM", "DASHCAM", "TRAIL_CAM"], help="Camera mode")
    args = parser.parse_args()

    director = AIPromptDirector()
    task = director.prepare_task(mode=args.mode)

    print("\n" + "=" * 70)
    print("🎬 GÓI KỊCH BẢN & DỮ LIỆU TẠO VIDEO AI 100% (KLING / HAILUO)")
    print("=" * 70)
    print(f"📌 Chủ đề: [{task['camera_mode']}] - {task['case_title']}")
    print(f"🖼️ Ảnh mồi (Start Frame): {task['start_frame_path']}")
    print("\n" + "-" * 70)
    print("👉 CÁCH TẠO BẰNG KLING AI (klingai.com) HOẶC HAILUO AI (hailuoai.video):")
    print("-" * 70)
    print("1. Mở trang: https://klingai.com (hoặc https://hailuoai.video)")
    print("2. Chọn chế độ: Image-to-Video (Tải ảnh mồi lên để giữ đúng bối cảnh)")
    print(f"   - Tải file ảnh: {task['start_frame_path']}")
    print(f"   - Paste Prompt sau vào:")
    print(f"\n   \"{task['kling_image_to_video_prompt']}\"\n")
    print("3. Negative Prompt:")
    print(f"   \"{task['negative_prompt']}\"")
    print(f"4. Motion Score: {task['recommended_motion']}")
    print("-" * 70)
    print("(Hoặc nếu bạn muốn Text-to-Video không cần ảnh, dùng Prompt này):")
    print(f"\"{task['kling_text_to_video_prompt']}\"")
    print("-" * 70)
    print("💡 Sau khi Kling/Hailuo sinh xong video (5s-10s):")
    print("   Bạn tải file video về và kéo vào thư mục:")
    print(f"   📂 c:\\Users\\ngu06\\Documents\\antigravity\\cam\\input_clips\\")
    print("   Sau đó chạy lệnh:")
    print(f"   python -m src.process_ai_video --task {task['task_id']}")
    print("   -> Bot sẽ tự động lồng âm thanh mic chân thực, đè HUD mili-giây, và tự đăng lên YouTube & Facebook!")
    print("=" * 70)

if __name__ == "__main__":
    main()
