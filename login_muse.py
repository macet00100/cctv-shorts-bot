import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
USER_DATA_DIR = BASE_DIR / "muse_browser_data"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 70)
    print("🔑 CÔNG CỤ ĐĂNG NHẬP VÀ LƯU PHIÊN LÀM VIỆC MUSE AI (31B TOKENS)")
    print("=" * 70)
    print(f"📁 Thư mục lưu dữ liệu trình duyệt: {USER_DATA_DIR}")
    print("\nĐang khởi động trình duyệt Chrome/Chromium...")

    with sync_playwright() as p:
        # Khởi động trình duyệt có giao diện (headless=False) với profile riêng
        launch_kwargs = {
            "user_data_dir": str(USER_DATA_DIR),
            "headless": False,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            "no_viewport": True
        }
        try:
            context = p.chromium.launch_persistent_context(channel="chrome", **launch_kwargs)
        except Exception:
            context = p.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else context.new_page()
        
        print("\n🌐 Đang mở trang web https://muse.ai ...")
        page.goto("https://muse.ai", wait_until="domcontentloaded")

        print("\n" + "*" * 70)
        print("👉 HƯỚNG DẪN:")
        print("1. Trình duyệt đã mở ra. Bạn hãy tiến hành ĐĂNG NHẬP vào tài khoản Meta của bạn.")
        print("2. Sau khi đăng nhập thành công vào được giao diện Chat của Muse AI (có hiển thị 31B token),")
        print("3. Bạn hãy quay lại cửa sổ Terminal này và NHẤN PHÍM ENTER để hoàn tất.")
        print("*" * 70 + "\n")

        try:
            input("Nhấn [ENTER] tại đây sau khi bạn đã đăng nhập thành công trên trình duyệt... ")
        except KeyboardInterrupt:
            print("\nĐã hủy.")
            context.close()
            return

        # Lưu lại cookies và storage state để tái sử dụng
        state_file = USER_DATA_DIR / "storage_state.json"
        context.storage_state(path=str(state_file))
        
        print(f"\n✅ ĐÃ LƯU TRẠNG THÁI PHIÊN ĐĂNG NHẬP THÀNH CÔNG VÀO:")
        print(f"   {state_file}")
        print("Bây giờ hệ thống có thể chạy ngầm (Headless) 24/24 mà không cần đăng nhập lại!")

        context.close()
        print("\nTrình duyệt đã đóng an toàn.")

if __name__ == "__main__":
    main()
