import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8080/"

captured_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global captured_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            captured_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <body style="font-family: Arial; text-align: center; padding-top: 50px; background: #121212; color: #fff;">
                <h1 style="color: #4CAF50;">🎉 XÁC THỰC THÀNH CÔNG!</h1>
                <p style="font-size: 18px;">Bạn có thể đóng tab này và quay lại cửa sổ chat.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received.")

    def log_message(self, format, *args):
        pass

def main():
    global CLIENT_ID, CLIENT_SECRET
    print("=" * 70)
    print("🔐 KHỞI ĐỘNG XÁC THỰC YOUTUBE OAUTH 2.0 (DIRECT FLOW)")
    print("=" * 70)

    if not CLIENT_ID:
        CLIENT_ID = input("👉 Nhập YOUTUBE_CLIENT_ID: ").strip()
    if not CLIENT_SECRET:
        CLIENT_SECRET = input("👉 Nhập YOUTUBE_CLIENT_SECRET: ").strip()

    server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
    print("📡 Đang lắng nghe tại http://localhost:8080/ ...")

    while captured_code is None:
        server.handle_request()

    print("\n✅ Đã bắt được Authorization Code từ Google!")
    print("🔄 Đang gửi mã để đổi lấy REFRESH TOKEN vĩnh viễn...")

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": captured_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    resp = requests.post(token_url, data=payload, timeout=20)
    data = resp.json()

    if "refresh_token" in data:
        refresh_token = data["refresh_token"]
        print("\n" + "=" * 70)
        print("🎉🎉🎉 XÁC THỰC THÀNH CÔNG! TOKEN ĐÃ ĐƯỢC TẠO:")
        print("=" * 70)
        print(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")

        env_path = Path(__file__).resolve().parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                env_content = f.read()

            env_content = env_content.replace("YOUTUBE_CLIENT_ID=", f"YOUTUBE_CLIENT_ID={CLIENT_ID}")
            env_content = env_content.replace("YOUTUBE_CLIENT_SECRET=", f"YOUTUBE_CLIENT_SECRET={CLIENT_SECRET}")
            env_content = env_content.replace("YOUTUBE_REFRESH_TOKEN=", f"YOUTUBE_REFRESH_TOKEN={refresh_token}")

            with open(env_path, "w", encoding="utf-8") as f:
                f.write(env_content)
            print("\n✅ ĐÃ TỰ ĐỘNG CẬP NHẬT VÀO FILE .env!")

        with open("youtube_tokens.txt", "w", encoding="utf-8") as f:
            f.write(f"YOUTUBE_CLIENT_ID={CLIENT_ID}\n")
            f.write(f"YOUTUBE_CLIENT_SECRET={CLIENT_SECRET}\n")
            f.write(f"YOUTUBE_REFRESH_TOKEN={refresh_token}\n")

        print("✅ ĐÃ LƯU VÀO FILE: youtube_tokens.txt")
    else:
        print(f"❌ Lỗi đổi token: {data}")

if __name__ == "__main__":
    main()
