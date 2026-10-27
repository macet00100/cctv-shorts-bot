import argparse
import sys
import time
from pathlib import Path

# Safe Unicode output for Windows/Linux CI
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.config import TARGET_DURATION, VIDEO_PROVIDER, OUTPUT_DIR
from src.viral_scheduler import ViralScheduler
from src.ai_story_director import AIStoryDirector
from src.footage_engine import FootageEngine
from src.image_generator import FoundFootageImageGenerator
from src.voice_audio_engine import AuthenticCameraAudioEngine
from src.video_engine import FoundFootageVideoEngine
from src.muse_video_engine import MuseVideoEngine
from src.youtube_uploader import YouTubeShortsUploader
from src.facebook_uploader import FacebookReelsUploader
from src.community_responder import AICommunityEngagementBot

def cleanup_storage(output_dir: Path, keep_latest: int = 5, max_age_days: int = 3):
    """Tự động dọn dẹp các video và ảnh cũ để chống đầy bộ nhớ."""
    if not output_dir.exists():
        return
    try:
        now_ts = time.time()
        max_age_sec = max_age_days * 86400
        files = [p for p in output_dir.glob("*") if p.is_file() and p.suffix.lower() in [".mp4", ".wav", ".png", ".jpg"]]
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        for idx, f in enumerate(files):
            age_sec = now_ts - f.stat().st_mtime
            if idx >= keep_latest or age_sec > max_age_sec:
                try:
                    f.unlink()
                    print(f"[STORAGE CLEANUP] 🧹 Đã dọn dẹp file cũ: {f.name}")
                except Exception:
                    pass
    except Exception as e:
        print(f"[STORAGE CLEANUP] Notice: {e}")

def main():
    parser = argparse.ArgumentParser(description="24/7 AI Found Footage Video Production Pipeline")
    parser.add_argument("--check-freshness", type=int, default=90, help="Minutes cooldown check (default: 90)")
    parser.add_argument("--force", action="store_true", help="Bypass freshness cooldown check")
    parser.add_argument("--mode", type=str, choices=["CCTV", "BODYCAM", "DASHCAM", "TRAIL_CAM"], help="Force specific camera mode")
    parser.add_argument("--dry-run", action="store_true", help="Generate video without uploading")
    parser.add_argument("--engagement-only", action="store_true", help="Run only the community comment engagement bot")
    args = parser.parse_args()

    print("=" * 70)
    print("🎬 24/7 AI FOUND FOOTAGE & SURVEILLANCE VIDEO AUTOMATION")
    print(f"⏱️ Video Duration Target: {TARGET_DURATION}s | Real Motion Engine V2")
    print("=" * 70)

    # If engagement only requested
    if args.engagement_only:
        bot = AICommunityEngagementBot()
        bot.run_engagement_cycle()
        return

    # Dọn dẹp sơ bộ bộ nhớ trước khi tạo video mới
    cleanup_storage(OUTPUT_DIR, keep_latest=5, max_age_days=3)

    # Step 1: Kiểm tra lịch ngẫu nhiên Viral Quốc Tế trong ngày
    scheduler = ViralScheduler()
    should_run, sched_reason, sched_info = scheduler.check_execution_status(force=args.force)
    print(f"\n[VIRAL SCHEDULER CHECK] {sched_reason}")
    if not should_run:
        print(f"[PIPELINE EXIT] Chưa đến khung giờ đăng random hôm nay hoặc đã hoàn thành. Tự động thoát.")
        sys.exit(0)

    # Step 2: Initialize AI Director & Layer 1 Guard
    director = AIStoryDirector()
    if not args.force:
        is_fresh = director.check_freshness(cooldown_minutes=args.check_freshness)
        if not is_fresh:
            print("[PIPELINE EXIT] Execution skipped by Layer 1 Freshness Guard. Video recently published.")
            sys.exit(0)

    # Step 3: Layer 2 & 3 AI Story Direction & Validation
    print("\n>>> PHASE 1: STORY DIRECTION & 4-LAYER MATRIX VALIDATION")
    scenario = director.generate_scenario(override_mode=args.mode)
    print(f"📌 Case: {scenario.get('case_title')}")
    print(f"📹 Mode: {scenario.get('camera_mode')} | Location: {scenario.get('location_type')} | Anomaly: {scenario.get('anomaly_type')}")

    # Step 3: Video Acquisition (Muse AI 31B Token or Fallback)
    print(f"\n>>> PHASE 2: VIDEO ACQUISITION (PROVIDER: {VIDEO_PROVIDER})")
    base_source_path = None

    if VIDEO_PROVIDER == "MUSE":
        muse_engine = MuseVideoEngine(headless=True)
        if muse_engine.is_configured():
            try:
                base_source_path = muse_engine.generate_video(scenario)
                print(f"🎬 Muse AI 31B Video Generated: {base_source_path.name}")
            except Exception as e:
                print(f"⚠️ Muse AI generation error ({e}), falling back to footage engine...")

    if not base_source_path:
        footage_engine = FootageEngine()
        try:
            base_source_path = footage_engine.acquire_footage(scenario, target_duration=TARGET_DURATION)
            print(f"📹 Real Base Video Footage Ready: {base_source_path.name}")
        except Exception as e:
            print(f"⚠️ Real footage fetch failed ({e}), falling back to FLUX image generator...")
            img_gen = FoundFootageImageGenerator()
            base_source_path = img_gen.generate(scenario)
            print(f"🖼️ Fallback Image Frame Ready: {base_source_path.name}")

    # Step 4 & 5: Video Preparation (20s Clean Viral Short - 100% Pure Muse AI, No Extra HUD)
    print(f"\n>>> PHASE 3 & 4: PREPARING 20S VIRAL SHORT (100% PURE MUSE AI)")
    if VIDEO_PROVIDER == "MUSE" and base_source_path and base_source_path.suffix.lower() == ".mp4":
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        final_video_path = OUTPUT_DIR / f"clean_short_{scenario.get('camera_mode', 'CCTV')}_{int(time.time())}.mp4"
        print(f"[CLEAN PIPELINE] Extending 10s Muse AI video to 20s via Slow-Mo Replay (No artificial text)...")
        import subprocess
        clean_cmd = [
            "ffmpeg", "-y",
            "-i", str(base_source_path),
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
            str(final_video_path)
        ]
        res = subprocess.run(clean_cmd, capture_output=True, text=True)
        if not final_video_path.exists() or final_video_path.stat().st_size == 0:
            print(f"[CLEAN PIPELINE] ⚠️ FFmpeg notice, using raw base video: {base_source_path.name}")
            final_video_path = base_source_path
    else:
        audio_engine = AuthenticCameraAudioEngine()
        master_audio_path = audio_engine.build_audio(scenario, duration=TARGET_DURATION)
        video_engine = FoundFootageVideoEngine()
        final_video_path = video_engine.render(base_source_path, master_audio_path, scenario)

    print(f"🎥 Final Video Ready for Publishing: {final_video_path}")

    # Step 6: Multi-platform Upload
    yt_id = None
    fb_id = None

    if args.dry_run:
        print("\n>>> PHASE 5: DRY RUN ACTIVE - SKIPPING UPLOADS.")
    else:
        print("\n>>> PHASE 5: MULTI-PLATFORM AUTO-PUBLISHING & COMMUNITY SETUP")
        # YouTube Shorts
        yt_uploader = YouTubeShortsUploader()
        yt_id = yt_uploader.upload(final_video_path, scenario)

        # Facebook Reels
        fb_uploader = FacebookReelsUploader()
        fb_id = fb_uploader.upload(final_video_path, scenario)

    # Step 7: Layer 4 Persistent History Recording & Daily Schedule Update
    if not args.dry_run:
        director.record_completed_post(scenario, yt_id=yt_id, fb_id=fb_id)
        scheduler.mark_completed(video_title=scenario.get("case_title"), yt_id=yt_id, fb_id=fb_id)
    else:
        print("[DRY RUN] Bỏ qua ghi nhận history và cập nhật lịch hoàn thành.")

    print("\n" + "=" * 70)
    print("✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"📁 Video: {final_video_path}")
    if yt_id:
        print(f"▶️ YouTube Shorts: https://youtube.com/shorts/{yt_id}")
    if fb_id:
        print(f"📘 Facebook Reel: Video ID {fb_id}")
    print("=" * 70)

if __name__ == "__main__":
    main()
