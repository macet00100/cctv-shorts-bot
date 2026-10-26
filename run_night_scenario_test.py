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

# 1. Xác định thời gian thực tế chính xác khi bắt đầu render
now = datetime.now()
current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
hour = now.hour
is_night = (hour < 6 or hour >= 18)
period_desc = "Nighttime scene in the dark hours at 04:00 AM" if is_night else "Daytime scene with bright daylight"
lighting_desc = "Dark night atmosphere illuminated by glowing street lamps, quiet dark city street at night" if is_night else "Bright natural sunlight and bustling daylight atmosphere"

location = "Times Square, New York"
case_title = f"{location} - {now.strftime('%d/%m/%Y')}"
raw_output = output_dir / f"raw_night_{int(time.time())}.mp4"
final_20s_output = output_dir / "NIGHT_TIMES_SQUARE_20S_FINAL.mp4"

# 2. Xây dựng prompt đêm với thời gian thực tế chính xác
prompt = (
    f"Create a vertical 9:16 aspect ratio security camera video. "
    f"Portrait orientation 9:16 framing. "
    f"{period_desc}. {lighting_desc}. "
    f"High-angle security camera view overlooking a storefront on {location} at night. "
    f"A quiet empty outdoor cafe patio in the dead of night, suddenly a metal cafe chair slides smoothly across the pavement by itself for 3 feet with nobody around, street light flickers once. "
    f"Authentic surveillance camera optics, realistic physics, dark ambient city night audio. "
    f"The on-screen camera timestamp displays exact real-time: {current_time_str}. "
    f"Vertical format 9:16."
)

print("=" * 70)
print(f"🌙 BẮT ĐẦU RENDER VIDEO BAN ĐÊM (THEO GIỜ THỰC TẾ: {current_time_str})")
print(f"📍 Bối cảnh: BAN ĐÊM tại {location}")
print(f"📝 Prompt gửi Muse AI:\n{prompt}")
print("=" * 70)

js_extract = """
async (url) => {
    const res = await fetch(url);
    const blob = await res.blob();
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

    # Đếm số lượng video đang có trên trang
    initial_video_count = page.locator("video").count()
    print(f"Số video hiện có trên trang trước khi gửi prompt: {initial_video_count}")

    # Gửi prompt mới
    ta = page.locator("textarea").first
    ta.click()
    ta.fill(prompt)
    page.wait_for_timeout(1000)
    ta.press("Enter")
    print("🚀 Đã gửi prompt ban đêm sang Muse AI! Đang chờ AI hoàn tất...")

    new_video_found = False
    start_time = time.time()
    timeout = 240

    while (time.time() - start_time) < timeout:
        page.wait_for_timeout(5000)
        elapsed = int(time.time() - start_time)

        # Kiểm tra xem thông báo "ready" đã xuất hiện chưa
        page_text = page.locator("body").inner_text()
        current_videos = page.locator("video").all()

        # Khi Muse render xong, video mới sẽ xuất hiện (tổng số video tăng lên)
        if len(current_videos) > initial_video_count:
            print(f"[{elapsed}s] 🎯 Phát hiện video mới xuất hiện trên trang! Đang kiểm tra blob...")
            # Video mới thường nằm ở vị trí thứ 3 hoặc gần cuối (trước 2 avatar)
            for v in current_videos:
                src = v.get_attribute("src")
                if not src or not src.startswith("blob:"):
                    continue
                try:
                    data_url = page.evaluate(js_extract, src)
                    if data_url and data_url.startswith("data:video/mp4;base64,"):
                        header, encoded = data_url.split(",", 1)
                        raw = base64.b64decode(encoded)
                        # Video AI thường có dung lượng trên 2MB (khác với avatar ~300KB)
                        if len(raw) > 2000000:
                            # Lưu thử và kiểm tra nếu là video mới
                            with open(raw_output, "wb") as f:
                                f.write(raw)
                            print(f"✅ Đã trích xuất video: {raw_output.name} ({len(raw) / 1024 / 1024:.2f} MB)")
                            new_video_found = True
                            break
                except Exception:
                    pass

        if new_video_found and elapsed > 30:
            # Đảm bảo video đã hoàn tất render hoàn toàn (ít nhất 35s)
            break

        if elapsed % 15 == 0:
            print(f"... Đang render video ban đêm ({elapsed}s / {timeout}s) ...")

    ctx.close()

if not new_video_found or not raw_output.exists() or raw_output.stat().st_size < 500000:
    print("❌ Lỗi: Chưa lấy được video mới từ Muse AI.")
    sys.exit(1)

# Kiểm tra độ phân giải của video ban đêm
probe_cmd = [
    "ffprobe", "-v", "error",
    "-show_entries", "stream=width,height,duration",
    "-of", "json", str(raw_output)
]
probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
print("\nThông tin video ban đêm vừa render:")
print(probe_res.stdout)

# Kéo dài thành video 20.0s sạch (0s-10s ban đầu, 10s-20s quay chậm hiện tượng kỳ bí, không dán chữ)
print("\n🎞️ Đang kéo dài thành 20.0s sạch (Tua chậm 0.5x đoạn ghế tự di chuyển ban đêm)...")
clean_cmd = [
    "ffmpeg", "-y",
    "-i", str(raw_output),
    "-filter_complex",
    "[0:v]trim=start=0:end=10,setpts=PTS-STARTPTS[v1]; [0:v]trim=start=2.5:end=7.5,setpts=2*(PTS-STARTPTS)[v2]; [v1][v2]concat=n=2:v=1:a=0[v]; [0:a]aloop=loop=-1:size=24000*10[a]",
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

if final_20s_output.exists() and final_20s_output.stat().st_size > 100000:
    print(f"\n🎉 HOÀN TẤT THÀNH CÔNG! Video BAN ĐÊM 20 giây đã sẵn sàng:")
    print(f"   Đường dẫn: {final_20s_output.resolve()}")
    print(f"   Dung lượng: {final_20s_output.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Tiêu đề bài đăng: {case_title} #shorts")
else:
    print("❌ Lỗi khi render video 20s.")
