import base64
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

output_raw = Path("output/times_square_night_raw.mp4")

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

    videos = page.locator("video").all()
    print(f"Tổng số video trên trang: {len(videos)}")

    # Duyệt qua các video và lấy video mới nhất (Video #3 trong thread chat)
    # Các video:
    # 0: CCTV cũ (horizontal)
    # 1: Shibuya cũ (vertical)
    # 2: Santa monica cũ (dashcam)
    # 3: Times Square BAN ĐÊM MỚI!
    # 4, 5: Avatar
    target_video = videos[2]
    src = target_video.get_attribute("src")
    print(f"Trích xuất Video 2 (Night Times Square): {src}")
    data_url = page.evaluate(js_extract, src)
    header, encoded = data_url.split(",", 1)
    raw = base64.b64decode(encoded)
    with open(output_raw, "wb") as f:
        f.write(raw)
    print(f"🎉 Đã lưu video BAN ĐÊM raw: {output_raw} ({len(raw) / 1024 / 1024:.2f} MB)")
    ctx.close()
