import argparse
import glob
import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Safe Unicode output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config import (
    BASE_DIR,
    OUTPUT_DIR,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    TARGET_DURATION,
    MONO_FONT_PATH
)
from src.voice_audio_engine import AuthenticCameraAudioEngine
from src.ai_story_director import AIStoryDirector
from src.youtube_uploader import YouTubeShortsUploader
from src.facebook_uploader import FacebookReelsUploader

INPUT_CLIPS_DIR = BASE_DIR / "input_clips"
AI_TASKS_DIR = BASE_DIR / "ai_tasks"

class AIClipProcessor:
    """
    Transforms raw 5-10s AI video clips (from Kling AI / Hailuo AI)
    into a complete 20-25s Found Footage short video with:
    - Cinematic 3-act pacing (Baseline -> AI Climax -> Tense Aftermath).
    - Authentic near-mic foley sound design (breathing, 60Hz hum, wind, startle gasp).
    - Digital surveillance HUD with live milliseconds HH:MM:SS.mmm & [● REC].
    - Direct auto-upload to YouTube Shorts and Facebook Reels.
    """

    def __init__(self):
        self.width = VIDEO_WIDTH
        self.height = VIDEO_HEIGHT
        self.fps = VIDEO_FPS
        self.target_duration = TARGET_DURATION  # 24.0s
        self.output_dir = OUTPUT_DIR

        try:
            self.font_hud = ImageFont.truetype(str(MONO_FONT_PATH), 32)
            self.font_clock = ImageFont.truetype(str(MONO_FONT_PATH), 40)
        except Exception:
            self.font_hud = ImageFont.load_default()
            self.font_clock = ImageFont.load_default()

    def process(self, input_video_path: Path, task_data: dict = None, dry_run: bool = False, skip_upload: bool = False) -> Path:
        print("\n" + "=" * 70)
        print(f"🎬 PROCESSING 100% AI VIDEO CLIP: {input_video_path.name}")
        print("=" * 70)

        # 1. Load or Generate Scenario Metadata
        if not task_data:
            director = AIStoryDirector()
            task_data = director.generate_scenario(override_mode="CCTV")

        camera_mode = task_data.get("camera_mode", "CCTV")
        case_title = task_data.get("case_title", "Unexplained Security Footage")
        print(f"📌 Case: {case_title} | Mode: {camera_mode}")

        # 2. Synthesize Authentic Near-Mic Foley Audio (Duration: 24s)
        audio_engine = AuthenticCameraAudioEngine()
        master_audio_path = audio_engine.build_audio(task_data, duration=self.target_duration)
        print(f"🔊 Master Foley Audio: {master_audio_path.name}")

        # 3. Read input AI clip
        cap = cv2.VideoCapture(str(input_video_path))
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        src_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        src_duration = src_count / src_fps if src_fps > 0 else 5.0
        print(f"📹 Source AI Video: {src_duration:.1f}s | {src_count} frames @ {src_fps:.1f} FPS")

        # Read all source frames into memory
        source_frames = []
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            source_frames.append(frame)
        cap.release()

        if not source_frames:
            raise RuntimeError(f"Could not read any frames from: {input_video_path}")

        # 4. Render 24s Output Video with Pacing Engine
        total_frames = int(self.target_duration * self.fps)
        output_video_path = self.output_dir / f"ai_rendered_{camera_mode}_{int(time.time())}.mp4"

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "bgr24",
            "-r", str(self.fps),
            "-i", "-",
            "-i", str(master_audio_path),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "19",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video_path)
        ]

        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Precompute scanlines mask
        scanlines = np.ones((self.height, self.width, 3), dtype=np.float32)
        scanlines[0::3, :, :] = 0.90
        scanlines[1::3, :, :] = 0.95

        start_time_base = datetime.now()
        hud_loc = task_data.get("hud_text_location", "SECTOR 04")
        hud_extra = task_data.get("simulated_hud_extra", "REC [●]")

        # Pacing structure for 24s:
        # Act 1 (0.0s - 4.5s): Mundane baseline hold on start frame with subtle camera breathe
        # Act 2 (4.5s - 16.5s): Full AI Motion clip (playback smoothly mapped over 12s)
        # Act 3 (16.5s - 24.0s): Tense linger on final frame with micro-jitter
        act1_frames = int(4.5 * self.fps)
        act2_frames = int(12.0 * self.fps)
        act3_frames = total_frames - (act1_frames + act2_frames)

        for frame_idx in range(total_frames):
            current_time_sec = frame_idx / float(self.fps)

            # Select frame according to 3-act pacing
            if frame_idx < act1_frames:
                # Act 1: Hold on first frame with subtle push-in
                raw_frame = source_frames[0]
            elif frame_idx < act1_frames + act2_frames:
                # Act 2: Play through the AI motion clip smoothly
                clip_prog = (frame_idx - act1_frames) / float(act2_frames)
                src_idx = int(clip_prog * (len(source_frames) - 1))
                raw_frame = source_frames[min(src_idx, len(source_frames) - 1)]
            else:
                # Act 3: Hold on last frame (aftermath)
                raw_frame = source_frames[-1]

            # 1. Crop/Scale to 1080x1920
            frame = self._crop_to_vertical(raw_frame)

            # 2. Camera micro-tracking & shake
            frame = self._apply_camera_breathe(frame, current_time_sec, camera_mode)

            # 3. Scanlines and analog noise
            frame = (frame.astype(np.float32) * scanlines).astype(np.uint8)
            noise = np.random.randint(-7, 7, (self.height, self.width, 3), dtype=np.int16)
            frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

            # 4. Minimal HUD with live milliseconds
            frame = self._render_minimal_hud(
                frame, frame_idx, current_time_sec, camera_mode, hud_loc, hud_extra, start_time_base
            )

            process.stdin.write(frame.tobytes())

            if frame_idx % 90 == 0:
                pct = (frame_idx / total_frames) * 100
                print(f"[PROCESSOR] Rendering: {pct:.1f}% ({frame_idx}/{total_frames} frames)")

        process.stdin.close()
        process.wait()

        print(f"✅ FINAL 100% AI VIDEO RENDERED: {output_video_path}")

        # 5. Multi-platform Auto Upload
        yt_id = None
        fb_id = None
        if skip_upload or dry_run:
            if skip_upload:
                print("\n[PROCESSOR] Skip upload flag active. Returning rendered video path.")
            else:
                print("\n[DRY RUN] Skipping social uploads.")
        else:
            print("\n>>> UPLOADING TO YOUTUBE SHORTS...")
            try:
                yt_uploader = YouTubeShortsUploader()
                yt_id = yt_uploader.upload(output_video_path, task_data)
                print(f"▶️ YouTube Shorts: https://youtube.com/shorts/{yt_id}")
            except Exception as e:
                print(f"⚠️ YouTube upload error: {e}")

        return output_video_path

    def _crop_to_vertical(self, frame: np.ndarray) -> np.ndarray:
        fh, fw = frame.shape[:2]
        target_aspect = self.width / float(self.height)
        current_aspect = fw / float(fh)

        if current_aspect > target_aspect:
            crop_w = int(fh * target_aspect)
            start_x = max(0, (fw - crop_w) // 2)
            cropped = frame[:, start_x:start_x + crop_w]
        else:
            crop_h = int(fw / target_aspect)
            start_y = max(0, (fh - crop_h) // 2)
            cropped = frame[start_y:start_y + crop_h, :]

        return cv2.resize(cropped, (self.width, self.height), interpolation=cv2.INTER_LINEAR)

    def _apply_camera_breathe(self, frame: np.ndarray, t_sec: float, camera_mode: str) -> np.ndarray:
        if camera_mode == "BODYCAM":
            dx = 5 * math.sin(t_sec * 3.5)
            dy = 6 * abs(math.sin(t_sec * 3.5))
            rot = 0.3 * math.sin(t_sec * 2.5)
            zoom = 1.02 + 0.01 * math.sin(t_sec * 1.5)
        else:
            dx = 1.2 * math.sin(t_sec * 0.8)
            dy = 1.2 * math.cos(t_sec * 0.6)
            rot = 0.03 * math.sin(t_sec * 0.4)
            zoom = 1.01 + 0.005 * math.sin(t_sec * 0.5)

        cx = self.width / 2
        cy = self.height / 2
        M = cv2.getRotationMatrix2D((cx, cy), rot, zoom)
        M[0, 2] += dx
        M[1, 2] += dy

        return cv2.warpAffine(frame, M, (self.width, self.height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

    def _render_minimal_hud(
        self,
        frame: np.ndarray,
        frame_idx: int,
        t_sec: float,
        camera_mode: str,
        hud_loc: str,
        hud_extra: str,
        start_time_base: datetime
    ) -> np.ndarray:
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # 1. Blinking REC Indicator
        rec_blink = (int(t_sec * 2) % 2) == 0
        rec_color = (255, 30, 30) if rec_blink else (140, 140, 140)
        draw.text((60, 80), "● REC", font=self.font_clock, fill=rec_color)

        # 2. Top-Right Telemetry
        draw.text((self.width - 450, 80), hud_extra, font=self.font_hud, fill=(210, 210, 210))

        # 3. Bottom HUD: Live Millisecond Clock
        millis = int((frame_idx % self.fps) * (1000 / self.fps))
        clock_str = f"2026-10-25 02:41:{int(15 + t_sec):02d}.{millis:03d}"
        draw.text((60, self.height - 140), clock_str, font=self.font_clock, fill=(235, 235, 235))
        draw.text((60, self.height - 90), f"{hud_loc} | {camera_mode}", font=self.font_hud, fill=(175, 175, 175))

        # 4. Mode-specific telemetry
        if camera_mode == "DASHCAM":
            speed = 46 + int(math.sin(t_sec * 0.7) * 2)
            draw.text((self.width - 380, self.height - 140), f"SPEED: {speed} MPH", font=self.font_hud, fill=(235, 235, 235))
            draw.text((self.width - 380, self.height - 90), "GPS: 34.05°N 118.24°W", font=self.font_hud, fill=(175, 175, 175))
        elif camera_mode == "TRAIL_CAM":
            draw.text((self.width - 380, self.height - 140), "TEMP: 42°F / 6°C", font=self.font_hud, fill=(120, 240, 120))
            draw.text((self.width - 380, self.height - 90), "PIR MOTION: ACTIVE", font=self.font_hud, fill=(120, 240, 120))
        elif camera_mode == "BODYCAM":
            draw.text((self.width - 400, self.height - 140), "AXON BODY 3", font=self.font_hud, fill=(235, 235, 235))
            draw.text((self.width - 400, self.height - 90), "AUDIO ON [MIC]", font=self.font_hud, fill=(175, 175, 175))

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

def main():
    parser = argparse.ArgumentParser(description="Process 100% AI Video Clip (Kling / Hailuo) & Publish")
    parser.add_argument("--file", type=str, help="Specific mp4 file in input_clips/")
    parser.add_argument("--task", type=str, help="Task ID from ai_tasks/ (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Render without publishing")
    args = parser.parse_args()

    # Find video file
    target_file = None
    if args.file:
        target_file = Path(args.file)
    else:
        # Check input_clips directory
        clips = list(INPUT_CLIPS_DIR.glob("*.mp4")) + list(INPUT_CLIPS_DIR.glob("*.mov"))
        if clips:
            target_file = sorted(clips, key=lambda f: f.stat().st_mtime, reverse=True)[0]

    if not target_file or not target_file.exists():
        print("=" * 70)
        print("⚠️ CHƯA TÌM THẤY VIDEO AI NÀO TRONG THƯ MỤC 'input_clips/'!")
        print("=" * 70)
        print("👉 Hướng dẫn:")
        print("1. Tạo kịch bản và ảnh mồi bằng lệnh: python -m src.ai_prompt_generator")
        print("2. Vào https://klingai.com hoặc https://hailuoai.video tạo clip 5s-10s miễn phí.")
        print(f"3. Tải video về và kéo vào thư mục: {INPUT_CLIPS_DIR}")
        print("4. Chạy lại lệnh này: python -m src.process_ai_video")
        print("=" * 70)
        sys.exit(0)

    # Load task data if available
    task_data = None
    if args.task:
        task_json = AI_TASKS_DIR / f"{args.task}.json"
        if task_json.exists():
            with open(task_json, "r", encoding="utf-8") as f:
                task_data = json.load(f)

    processor = AIClipProcessor()
    processor.process(target_file, task_data=task_data, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
