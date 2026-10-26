import sys
from pathlib import Path

# Safe Unicode output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.muse_video_engine import MuseVideoEngine

def main():
    print("=" * 70)
    print("🎬 TEST TẠO THỬ 1 VIDEO VỚI MUSE AI (31B TOKENS WEB AUTOMATION)")
    print("=" * 70)

    # Chạy ở chế độ có giao diện (headless=False) để bạn có thể nhìn thấy trực tiếp bot thao tác!
    engine = MuseVideoEngine(headless=False)

    if not engine.is_configured():
        print("\n❌ Chưa có phiên đăng nhập Muse AI!")
        print("👉 Vui lòng chạy file 'DANG_NHAP_MUSE.bat' trước một lần duy nhất để lưu đăng nhập.")
        return

    test_scenario = {
        "camera_mode": "CCTV",
        "anomaly_type": "HEROIC_CLOSE_CALL",
        "case_title": "Test CCTV Heroic Save on Sidewalk"
    }

    try:
        video_path = engine.generate_video(test_scenario, timeout_seconds=300)
        print("\n" + "=" * 70)
        print(f"🎉 THÀNH CÔNG! Video đã được tải về tại:")
        print(f"   {video_path.resolve()}")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình tạo video: {e}")

if __name__ == "__main__":
    main()
