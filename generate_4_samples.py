import shutil
import sys
import time
from pathlib import Path

# Safe Unicode output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.ai_story_director import AIStoryDirector
from src.footage_engine import FootageEngine
from src.image_generator import FoundFootageImageGenerator
from src.voice_audio_engine import AuthenticCameraAudioEngine
from src.video_engine import FoundFootageVideoEngine
from src.config import OUTPUT_DIR, TARGET_DURATION

SAMPLE_SPECS = [
    ("DASHCAM", "HIGHWAY_TUNNEL", "3_DASHCAM_Highway_Sample.mp4", "Camera Hành Trình Ô Tô (Windshield Real Motion / Night Road)"),
    ("CCTV", "GAS_STATION_STORE", "1_CCTV_Security_Sample.mp4", "Camera Giám Sát An Ninh (Surveillance Real Motion / Night Lot)"),
    ("BODYCAM", "ABANDONED_FACILITY", "2_BODYCAM_Police_Sample.mp4", "Camera Đeo Ngực Cảnh Sát (First Person POV / Real Walking)"),
    ("TRAIL_CAM", "DEEP_FOREST", "4_TRAIL_CAM_Infrared_Sample.mp4", "Camera Bẫy Thú Rừng Đêm (Infrared Night Motion / Eye Shine)")
]

def generate_sample(mode: str, location: str, target_filename: str, description: str):
    print("\n" + "=" * 70)
    print(f"🎬 ĐANG TẠO VIDEO MẪU 24S CHUYỂN ĐỘNG THỰC [{mode}]: {description}")
    print("=" * 70)

    # 1. Story Director: 50/50 Ambiguity Scenario
    director = AIStoryDirector()
    scenario = director._procedural_fallback_scenario(mode, location, "UNKNOWN_CRYPTID")
    print(f"📌 Tiêu đề: {scenario.get('case_title')}")
    print(f"📍 Bối cảnh: {scenario.get('location_type')} | HUD: {scenario.get('hud_text_location')}")

    # 2. Authentic Video Footage Acquisition (Real Motion)
    footage_engine = FootageEngine()
    try:
        base_source_path = footage_engine.acquire_footage(scenario, target_duration=TARGET_DURATION)
        print(f"📹 Video gốc chuyển động thật: {base_source_path.name}")
    except Exception as e:
        print(f"⚠️ Footage fallback: {e}")
        img_gen = FoundFootageImageGenerator()
        base_source_path = img_gen.generate(scenario)

    # 3. Audio: Pure authentic camera ambient foley (Duration 24s)
    audio_engine = AuthenticCameraAudioEngine()
    master_audio_path = audio_engine.build_audio(scenario, duration=TARGET_DURATION)
    print(f"🔊 Âm thanh mic camera chân thực: {master_audio_path.name}")

    # 4. Video Engine: 24s Real-Motion Render + 50/50 Dynamic Moving Anomaly at 6.8s - 10.2s
    video_engine = FoundFootageVideoEngine()
    rendered_video_path = video_engine.render(base_source_path, master_audio_path, scenario)

    # 5. Copy to clean sample name
    final_sample_path = OUTPUT_DIR / target_filename
    shutil.copy2(rendered_video_path, final_sample_path)
    print(f"✅ ĐÃ XUẤT BẢN VIDEO MẪU THÀNH CÔNG: {final_sample_path.name}")
    return final_sample_path, scenario

def main():
    print("=" * 70)
    print(f"🎥 BẮT ĐẦU SẢN XUẤT BỘ 4 VIDEO MẪU ({TARGET_DURATION}S) CHUYỂN ĐỘNG THỰC TẾ 100%")
    print("   (Footage camera thật, Không giọng đọc, Không chữ banner, Dị tượng 50/50 di chuyển ở giây 7-10)")
    print("=" * 70)

    results = []
    start_total = time.time()

    for idx, (mode, loc, filename, desc) in enumerate(SAMPLE_SPECS, start=1):
        print(f"\n>>> [TIẾN ĐỘ: {idx}/4] ĐANG XỬ LÝ CHỦ ĐỀ: {mode}")
        path, scenario = generate_sample(mode, loc, filename, desc)
        results.append((mode, path, scenario))

    total_time = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"🎉 HOÀN THÀNH TOÀN BỘ 4 VIDEO MẪU TRONG {total_time:.1f} GIÂY!")
    print("=" * 70)
    print("Danh sách video trong thư mục 'output/' để bạn xem duyệt:")
    for mode, path, sc in results:
        print(f"👉 [{mode}]: {path}")
        print(f"   Tiêu đề: {sc.get('case_title')}")
        print(f"   Bình luận ghim: \"{sc.get('pinned_comment')}\"")

if __name__ == "__main__":
    main()
