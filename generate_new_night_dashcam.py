import base64
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)

# 1. Lấy chính xác thời gian thực tế bắt đầu render
now = datetime.now()
current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
hour = now.hour
is_night = (hour < 6 or hour >= 18)
period_desc = f"Nighttime scene in the dark hours at {now.strftime('%I:%M %p')}" if is_night else f"Daytime scene with bright natural daylight at {now.strftime('%I:%M %p')}"
lighting_desc = "Dark night atmosphere illuminated by glowing neon street lamps and car headlights, quiet dark avenue at night" if is_night else "Bright clear natural daylight, vibrant daytime street atmosphere"

location = "Downtown Las Vegas Boulevard"
date_title_str = now.strftime("%d/%m/%Y")
video_title = f"{location} - {date_title_str} #shorts"

raw_output = output_dir / f"vegas_dashcam_night_raw.mp4"
final_20s_output = output_dir / f"VEGAS_DASHCAM_NIGHT_20S_FINAL.mp4"

# 2. Xây dựng prompt đêm cho Dashcam với thời gian thực tế
prompt = (
    f"Create a vertical 9:16 aspect ratio car dashcam front windshield perspective video. "
    f"Portrait orientation 9:16 framing. "
    f"{period_desc}. {lighting_desc}. "
    f"Driving smoothly down {location} at night under streetlights. "
    f"Ahead on the dark asphalt, a colorful inflatable ball rolls into the lane under glowing headlights, driver smoothly brakes to a controlled stop letting the ball bounce safely to the curb. "
    f"Authentic windshield camera optics, realistic vehicle headlights beam on dark pavement, authentic engine and night road audio. "
    f"The on-screen camera timestamp displays exact real-time: {current_time_str}. "
    f"Vertical format 9:16."
)

print("=" * 75)
print(f"🌙 BẮT ĐẦU TẠO VIDEO MỚI THEO GIỜ THỰC TẾ: {current_time_str}")
print(f"🎬 Tiêu đề video: {video_title}")
print(f"📍 Bối cảnh: BAN ĐÊM tại {location}")
print(f"📝 Prompt gửi Muse AI:\n{prompt}")
print("=" * 75)

js_extract_blob = """
async (url) => {
    const res = await fetch(url);
    const blob = await res.blob();
    if (blob.size < 1000000) return null; // Bỏ qua avatar (~300KB)
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}
"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir="muse_browser_data",
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.pages[0]
    page.goto("https://muse.ai", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    # Ghi nhận danh sách tất cả blob URL hiện có trước khi gửi câu lệnh mới
    existing_videos = page.locator("video").all()
    existing_blob_urls = set()
    for v in existing_videos:
        src = v.get_attribute("src")
        if src and src.startswith("blob:"):
            existing_blob_urls.add(src)
    print(f"📊 Số lượng video blob hiện có trên trang: {len(existing_blob_urls)}")

    # Gửi prompt mới
    ta = page.locator("textarea").first
    ta.click()
    ta.fill(prompt)
    page.wait_for_timeout(1000)
    ta.press("Enter")
    print("🚀 Đã gửi câu lệnh sang Muse AI! Đang chờ tạo video...")

    start_time = time.time()
    timeout = 300
    new_video_saved = False

    while (time.time() - start_time) < timeout:
        page.wait_for_timeout(6000)
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed}s / {timeout}s] Đang kiểm tra tiến độ Muse AI...")

        current_videos = page.locator("video").all()
        # Tìm video có blob URL MỚI chưa từng xuất hiện trước đó
        for v in current_videos:
            src = v.get_attribute("src")
            if not src or not src.startswith("blob:"):
                continue
            if src not in existing_blob_urls:
                print(f"🎯 Phát hiện blob URL MỚI: {src}")
                try:
                    data_url = page.evaluate(js_extract_blob, src)
                    if data_url and data_url.startswith("data:video/mp4;base64,"):
                        header, encoded = data_url.split(",", 1)
                        raw = base64.b64decode(encoded)
                        if len(raw) > 1000000: # Đảm bảo là video AI (>1MB)
                            with open(raw_output, "wb") as f:
                                f.write(raw)
                            print(f"🎉 Đã bắt được video mới: {raw_output.name} ({len(raw) / 1024 / 1024:.2f} MB)")
                            new_video_saved = True
                            break
                        else:
                            print(f"⚠️ Blob mới nhưng kích thước nhỏ ({len(raw)} bytes), tiếp tục chờ...")
                except Exception as e:
                    print(f"Lỗi extract: {e}")

        if new_video_saved:
            break

    # Chụp ảnh debug nếu cần
    page.screenshot(path="output/latest_dashcam_state.png")
    ctx.close()

if not new_video_saved or not raw_output.exists():
    print("❌ Không lấy được video từ Muse AI!")
    sys.exit(1)

print("\n🎞️ BẮT ĐẦU XỬ LÝ 20S VIRAL SHORT (CLEAN REPLAY - 0% ARTIFICIAL HUD)...")
clean_cmd = [
    "ffmpeg", "-y",
    "-i", str(raw_output),
    "-filter_complex",
    "[0:v]trim=start=0:end=10,setpts=PTS-STARTPTS[v1]; [0:v]trim=start=3.0:end=8.0,setpts=2*(PTS-STARTPTS)[v2]; [v1][v2]concat=n=2:v=1:a=0[v]; [0:a]aloop=loop=-1:size=24000*10[a]",
    "-map", "[v]",
    "-map", "[a]",
    "-t", "20.0",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "18",
    "-c:a", "aac",
    "-b:a", "128k",
    str(final_20s_output)
]
subprocess.run(clean_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if final_20s_output.exists():
    size_mb = final_20s_output.stat().st_size / 1024 / 1024
    print(f"✅ HOÀN TẤT VIDEO MỚI: {final_20s_output.name} ({size_mb:.2f} MB)")
    print(f"🎬 Tiêu đề: {video_title}")

    # Trích xuất 2 frame ảnh để kiểm tra chất lượng & timestamp
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:02", "-i", str(final_20s_output), "-vframes", "1", "-q:v", "2", "output/vegas_preview_1.jpg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:14", "-i", str(final_20s_output), "-vframes", "1", "-q:v", "2", "output/vegas_preview_2.jpg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("📸 Đã trích xuất 2 ảnh xem trước: output/vegas_preview_1.jpg và output/vegas_preview_2.jpg")
else:
    print("❌ Lỗi khi render 20s final video!")
