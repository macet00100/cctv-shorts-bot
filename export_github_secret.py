import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

state_path = Path("muse_browser_data/storage_state.json")
if not state_path.exists():
    print("❌ Chưa tìm thấy file muse_browser_data/storage_state.json!")
    print("👉 Hãy chạy DANG_NHAP_MUSE.bat trước để đăng nhập.")
    sys.exit(1)

with open(state_path, "r", encoding="utf-8") as f:
    content = f.read().strip()

print("=" * 70)
print("🔑 NỘI DUNG GITHUB SECRET: MUSE_STORAGE_STATE")
print("=" * 70)
print("1. Vào GitHub Repo > Settings > Secrets and variables > Actions")
print("2. Nhấn 'New repository secret'")
print("3. Tên Secret: MUSE_STORAGE_STATE")
print("4. Giá trị Secret: Copy toàn bộ chuỗi JSON bên dưới dán vào:")
print("-" * 70)
print(content)
print("-" * 70)
print("✅ Khi đẩy lên GitHub, GitHub Actions sẽ dùng phiên đăng nhập này để chạy tự động 24/24!")
print("=" * 70)
