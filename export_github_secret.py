import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def load_env_file(filepath: Path = Path(".env")):
    env_vars = {}
    if not filepath.exists():
        return env_vars
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env_vars[key.strip()] = val.strip()
    return env_vars

print("=" * 75)
print("🛡️ CÔNG CỤ BẢO MẬT & XUẤT GITHUB SECRETS (KHÔNG LỘ CODE RA NGOÀI)")
print("=" * 75)
print("Khi đẩy dự án lên GitHub (kể cả Public hay Private repo):")
print("👉 Toàn bộ Key, Token, Mật khẩu PHẢI nằm trong 'GitHub Repository Secrets'.")
print("👉 Code trên repo sẽ KHÔNG chứa bất kỳ ký tự nhạy cảm nào!")
print("\nCác bước thêm Secrets vào GitHub:")
print("1. Vào GitHub Repo của bạn trên trình duyệt")
print("2. Chọn: Settings > Secrets and variables > Actions")
print("3. Nhấn nút xanh: 'New repository secret'")
print("=" * 75)

# 1. MUSE_STORAGE_STATE
state_path = Path("muse_browser_data/storage_state.json")
if state_path.exists():
    with open(state_path, "r", encoding="utf-8") as f:
        muse_val = f.read().strip()
    print("\n[SECRET 1] Tên: MUSE_STORAGE_STATE  (BẮT BUỘC ĐỂ CHẠY MUSE AI)")
    print("---------------------------------------------------------------------------")
    print(muse_val)
    print("---------------------------------------------------------------------------")
else:
    print("\n[SECRET 1] ⚠️ Chưa có muse_browser_data/storage_state.json! Hãy chạy DANG_NHAP_MUSE.bat trước.")

# 2. Đọc các secret từ .env
env_vars = load_env_file()
secret_names = [
    ("YOUTUBE_CLIENT_ID", "Client ID của Google Cloud API"),
    ("YOUTUBE_CLIENT_SECRET", "Client Secret của Google Cloud API"),
    ("YOUTUBE_REFRESH_TOKEN", "Mã Refresh Token vĩnh viễn YouTube Shorts"),
    ("FB_PAGE_ID", "ID Fanpage Facebook"),
    ("FB_PAGE_ACCESS_TOKEN", "Mã Access Token vĩnh viễn Facebook Reels")
]

for idx, (sec_name, desc) in enumerate(secret_names, start=2):
    val = env_vars.get(sec_name)
    if val and val != f"your_{sec_name.lower()}":
        print(f"\n[SECRET {idx}] Tên: {sec_name}  ({desc})")
        print("---------------------------------------------------------------------------")
        print(val)
        print("---------------------------------------------------------------------------")
    else:
        print(f"\n[SECRET {idx}] Tên: {sec_name} (Chưa cấu hình trong .env - Bỏ qua nếu chưa dùng)")

print("\n" + "=" * 75)
print("✅ SAU KHI THÊM XONG CÁC SECRET TRÊN, BẠN CÓ THỂ YÊN TÂM ĐẨY CODE LÊN GITHUB:")
print("   git remote add origin https://github.com/<tai-khoan>/<ten-repo>.git")
print("   git branch -M main")
print("   git push -u origin main")
print("=" * 75)
