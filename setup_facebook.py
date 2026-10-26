import os
import sys
import requests
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def main():
    print("=" * 70)
    print("📘 FACEBOOK REELS TOKEN SETUP & VERIFIER")
    print("=" * 70)

    page_id = input("\n👉 Nhập FB_PAGE_ID (ID của Fanpage): ").strip()
    token = input("👉 Nhập Facebook Token (lấy từ Graph API Explorer): ").strip()

    if not page_id or not token:
        print("❌ Page ID và Token không được để trống!")
        return

    # Check token validity and permissions
    print("\n🔍 Đang kiểm tra token với máy chủ Facebook...")
    url = f"https://graph.facebook.com/v19.0/{page_id}?fields=name,id,access_token&access_token={token}"
    resp = requests.get(url)
    data = resp.json()

    if "error" in data:
        print(f"❌ Facebook báo lỗi: {data['error'].get('message')}")
        print("Hãy đảm bảo bạn đã cấp quyền 'publish_video' và 'pages_manage_posts' cho Fanpage.")
        return

    page_name = data.get("name", "Unknown Page")
    print(f"✅ Kết nối thành công tới Fanpage: '{page_name}' (ID: {page_id})")

    # If the token passed was a user token that has a page access_token in response:
    final_token = data.get("access_token", token)

    # Update .env
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace("FB_PAGE_ID=", f"FB_PAGE_ID={page_id}")
        content = content.replace("FB_PAGE_ACCESS_TOKEN=", f"FB_PAGE_ACCESS_TOKEN={final_token}")

        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("\n✅ ĐÃ TỰ ĐỘNG CẬP NHẬT VÀO FILE .env!")

    with open("facebook_tokens.txt", "w", encoding="utf-8") as f:
        f.write(f"FB_PAGE_ID={page_id}\n")
        f.write(f"FB_PAGE_ACCESS_TOKEN={final_token}\n")

    print(f"✅ ĐÃ LƯU THÔNG TIN VÀO FILE: facebook_tokens.txt")
    print("\n🎉 FANPAGE CỦA BẠN ĐÃ SẴN SÀNG ĐĂNG REELS!")

if __name__ == "__main__":
    main()
