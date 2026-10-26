import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEDULE_FILE = BASE_DIR / "daily_viral_schedule.json"

# 4 Khung Giờ Vàng Quốc Tế Dễ Viral Nhất (Quy đổi sang Giờ Việt Nam GMT+7):
# 1. 07:00 - 09:30 VN: Giờ vàng đỉnh điểm Bắc Mỹ (US EST 8:00 PM - 10:30 PM, tối thư giãn xem Shorts)
# 2. 11:30 - 13:30 VN: Giờ vàng Bờ Tây Mỹ (US PST 9:30 PM - 11:30 PM) & Châu Á ăn trưa
# 3. 19:30 - 21:30 VN: Giờ vàng Châu Âu (UK/EU 1:30 PM - 3:30 PM / tối) & Giờ thức dậy kiểm tra điện thoại ở Mỹ (US 8:30 AM EST)
# 4. 23:30 - 01:30 VN: Giờ ăn trưa Bắc Mỹ (US EST 12:30 PM - 2:30 PM)
VIRAL_WINDOWS = [
    {
        "id": "US_PRIME_EVENING",
        "name": "Giờ Vàng Mỹ Buổi Tối (US EST 8:00 PM - 10:30 PM)",
        "start_hour": 7,
        "start_minute": 0,
        "end_hour": 9,
        "end_minute": 30
    },
    {
        "id": "US_WEST_COAST_LATE",
        "name": "Giờ Vàng Bờ Tây Mỹ (US PST 9:30 PM - 11:30 PM)",
        "start_hour": 11,
        "start_minute": 30,
        "end_hour": 13,
        "end_minute": 30
    },
    {
        "id": "EUROPE_PRIME_US_MORNING",
        "name": "Giờ Vàng Châu Âu & Sáng Sớm Mỹ (EU 8:00 PM / US 8:30 AM EST)",
        "start_hour": 19,
        "start_minute": 30,
        "end_hour": 21,
        "end_minute": 30
    },
    {
        "id": "US_LUNCH_BREAK",
        "name": "Giờ Ăn Trưa Bắc Mỹ (US EST 12:30 PM - 2:30 PM)",
        "start_hour": 23,
        "start_minute": 30,
        "end_hour": 25, # 01:30 sáng hôm sau
        "end_minute": 30
    }
]

class ViralScheduler:
    """
    Bộ lập lịch thông minh ngẫu nhiên khung giờ viral quốc tế mỗi ngày.
    - Mỗi ngày tự động chọn ngẫu nhiên 1 trong 4 khung giờ vàng quốc tế.
    - Random phút chính xác bên trong khung giờ đó (chống spam cố định).
    - Đảm bảo mỗi ngày chỉ đăng 1 video duy nhất vào thời điểm tối ưu nhất.
    """

    def __init__(self, schedule_file: Path = SCHEDULE_FILE):
        self.schedule_file = schedule_file

    def get_current_vn_time(self) -> datetime:
        """Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)."""
        utc_now = datetime.now(timezone.utc)
        vn_now = utc_now + timedelta(hours=7)
        return vn_now

    def load_schedule(self) -> Dict[str, Any]:
        if not self.schedule_file.exists():
            return {}
        try:
            with open(self.schedule_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_schedule(self, data: Dict[str, Any]):
        try:
            with open(self.schedule_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[SCHEDULER] Lỗi lưu lịch: {e}")

    def generate_daily_schedule(self, date_str: str) -> Dict[str, Any]:
        """
        Tạo lịch đăng ngẫu nhiên cho một ngày cụ thể (YYYY-MM-DD):
        Random 1 khung giờ trong 4 khung giờ vàng + Random phút ngẫu nhiên.
        """
        # Chọn ngẫu nhiên 1 trong 4 khung giờ vàng
        chosen_window = random.choice(VIRAL_WINDOWS)

        # Tính phút ngẫu nhiên bên trong khung giờ
        start_total_mins = chosen_window["start_hour"] * 60 + chosen_window["start_minute"]
        end_total_mins = chosen_window["end_hour"] * 60 + chosen_window["end_minute"]
        random_minute_of_day = random.randint(start_total_mins, end_total_mins)

        target_hour = (random_minute_of_day // 60) % 24
        target_minute = random_minute_of_day % 60
        target_time_str = f"{target_hour:02d}:{target_minute:02d}"

        schedule_data = {
            "date": date_str,
            "window_id": chosen_window["id"],
            "window_name": chosen_window["name"],
            "target_time_vn": target_time_str,
            "target_hour": target_hour,
            "target_minute": target_minute,
            "status": "PENDING",
            "created_at": self.get_current_vn_time().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.save_schedule(schedule_data)
        print(f"\n[VIRAL SCHEDULER] 🎯 ĐÃ LẬP LỊCH RANDOM CHO NGÀY {date_str}:")
        print(f"🌍 Khung giờ vàng chọn trúng: {chosen_window['name']}")
        print(f"⏰ Giờ đăng ngẫu nhiên chính xác: {target_time_str} (Giờ VN)")
        print(f"📌 Trạng thái: PENDING (Đang chờ đến giờ)\n")
        return schedule_data

    def check_execution_status(self, force: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Kiểm tra xem hiện tại có đúng thời điểm để render & xuất bản video không.
        Returns:
            should_run (bool): True nếu cần chạy ngay, False nếu bỏ qua.
            message (str): Lý do chi tiết.
            schedule_info (dict): Thông tin lịch của ngày hôm nay.
        """
        vn_now = self.get_current_vn_time()
        today_str = vn_now.strftime("%Y-%m-%d")
        current_time_str = vn_now.strftime("%H:%M")

        schedule = self.load_schedule()

        # Nếu chưa có lịch cho ngày hôm nay -> Tạo lịch mới ngẫu nhiên
        if schedule.get("date") != today_str:
            schedule = self.generate_daily_schedule(today_str)

        if force:
            return True, f"Bỏ qua lịch hẹn (Force=True) - Kích hoạt ngay lúc {current_time_str} VN", schedule

        # Nếu hôm nay đã hoàn thành đăng video
        if schedule.get("status") == "COMPLETED":
            post_title = schedule.get("completed_video_title", "Unknown")
            return False, f"Hôm nay ({today_str}) đã đăng video viral thành công ('{post_title}'). Nghỉ ngơi đến ngày mai!", schedule

        target_hour = schedule.get("target_hour", 8)
        target_minute = schedule.get("target_minute", 0)
        target_total_mins = target_hour * 60 + target_minute
        current_total_mins = vn_now.hour * 60 + vn_now.minute

        # Nếu chưa đến giờ
        if current_total_mins < target_total_mins:
            diff_mins = target_total_mins - current_total_mins
            target_str = schedule.get("target_time_vn")
            window_name = schedule.get("window_name")
            return False, f"Chưa đến giờ đăng hôm nay (Mục tiêu: {target_str} VN | Còn {diff_mins} phút | Khung: {window_name})", schedule

        # Đã đến hoặc vượt qua giờ hẹn (trong cùng ngày và chưa đăng)
        target_str = schedule.get("target_time_vn")
        return True, f"ĐÃ ĐẾN GIỜ VÀNG QUỐC TẾ ({target_str} VN)! Kích hoạt tạo & đăng video ngay!", schedule

    def mark_completed(self, video_title: str, yt_id: str = None, fb_id: str = None):
        """Đánh dấu ngày hôm nay đã đăng video thành công."""
        schedule = self.load_schedule()
        vn_now = self.get_current_vn_time()
        schedule["status"] = "COMPLETED"
        schedule["completed_at"] = vn_now.strftime("%Y-%m-%d %H:%M:%S")
        schedule["completed_video_title"] = video_title
        schedule["youtube_id"] = yt_id
        schedule["facebook_id"] = fb_id
        self.save_schedule(schedule)
        print(f"\n[VIRAL SCHEDULER] ✅ Đã hoàn tất và lưu trạng thái đăng bài ngày {schedule.get('date')}: '{video_title}'")


if __name__ == "__main__":
    scheduler = ViralScheduler()
    force_run = "--force" in sys.argv
    check_only = "--check-only" in sys.argv

    should_run, reason, sched = scheduler.check_execution_status(force=force_run)
    print("=" * 70)
    print(f"🕒 Giờ Việt Nam hiện tại: {scheduler.get_current_vn_time().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Lịch hôm nay ({sched.get('date')}): Giờ hẹn {sched.get('target_time_vn')} VN | Trạng thái: {sched.get('status')}")
    print(f"📢 Kết quả kiểm tra: {'[CHẠY NGAY]' if should_run else '[BỎ QUA CA]'}")
    print(f"💬 Chi tiết: {reason}")
    print("=" * 70)

    # Set GitHub Actions output parameter if running in CI
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"should_run={'true' if should_run else 'false'}\n")
            f.write(f"target_time={sched.get('target_time_vn')}\n")

    if not should_run and not force_run:
        sys.exit(0)
