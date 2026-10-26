import math
import os
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Union

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config import (
    OUTPUT_DIR,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    MONO_FONT_PATH
)

class FoundFootageVideoEngine:
    """
    Cinematic Raw Found Footage Video Engine (V2 - Real Motion Footage Core).
    - Uses authentic 1080p camera video footage (Dashcam, Bodycam, CCTV, Trail Cam).
    - 0.0s - 6.8s: Quiet, completely normal, mundane baseline footage (cars driving, trees swaying, camera walking).
    - 6.8s - 10.2s: CLIMAX: Subtle 50/50 anomaly moves physically across the scene + reactive camera tracking!
    - 10.2s - 24.0s: Tense aftermath linger, camera breathing, leaving 50/50 ambiguous debate.
    - Authentic HUD: Milliseconds timestamp, flashing [● REC], camera hardware telemetry.
    - NO narrator voice, NO text overlays/banners, NO artificial red circles.
    """

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.width = VIDEO_WIDTH
        self.height = VIDEO_HEIGHT
        self.fps = VIDEO_FPS
        self.font_path = MONO_FONT_PATH

        try:
            self.font_hud = ImageFont.truetype(str(self.font_path), 32)
            self.font_clock = ImageFont.truetype(str(self.font_path), 40)
        except Exception:
            self.font_hud = ImageFont.load_default()
            self.font_clock = ImageFont.load_default()

    def render(self, base_source_path: Path, master_audio_path: Path, scenario: Dict[str, Any]) -> Path:
        """
        Renders a high-definition 20-30s found footage short video.
        Accepts either a raw video file (.mp4) or fallback image (.png/.jpg).
        """
        print(f"[VIDEO ENGINE] Initializing real-motion render pipeline with: {base_source_path.name}...")
        duration = self._get_audio_duration(master_audio_path)
        total_frames = int(duration * self.fps)
        print(f"[VIDEO ENGINE] Duration: {duration:.2f}s | Total Frames: {total_frames} @ {self.fps} FPS")

        output_video_path = self.output_dir / f"final_{scenario.get('camera_mode', 'CCTV')}_{int(time.time())}.mp4"

        # Check if source is video or image
        is_video_source = base_source_path.suffix.lower() in [".mp4", ".mov", ".avi", ".webm", ".mkv"]
        cap = None
        base_img = None

        if is_video_source:
            cap = cv2.VideoCapture(str(base_source_path))
            if not cap.isOpened():
                print(f"[VIDEO ENGINE] Failed to open video {base_source_path}, falling back to static generation...")
                is_video_source = False
        
        if not is_video_source:
            base_img = cv2.imread(str(base_source_path))
            if base_img is None:
                base_img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            else:
                base_img = cv2.resize(base_img, (self.width, self.height))

        # Target anomaly coordinates
        target_coords = scenario.get("red_circle_target", [0.45, 0.50, 0.12])
        tx = int(target_coords[0] * self.width)
        ty = int(target_coords[1] * self.height)
        tr = int(target_coords[2] * self.width)

        camera_mode = scenario.get("camera_mode", "CCTV")
        hud_loc = scenario.get("hud_text_location", "SECTOR 04")
        hud_extra = scenario.get("simulated_hud_extra", "REC [●]")

        # Prepare FFmpeg pipe
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
            "-crf", "20",
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

        for frame_idx in range(total_frames):
            current_time_sec = frame_idx / float(self.fps)

            # 1. Fetch current background frame
            if is_video_source:
                ret, raw_frame = cap.read()
                if not ret or raw_frame is None:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, raw_frame = cap.read()
                
                # Crop and resize raw_frame to vertical 9:16 (1080x1920)
                frame = self._crop_to_vertical(raw_frame)
            else:
                frame = base_img.copy()

            # 2. Inject Dynamic 50/50 Moving Anomaly at 6.8s - 10.2s
            frame = self._inject_dynamic_anomaly(frame, current_time_sec, tx, ty, tr, camera_mode)

            # 3. Camera Tracking & Whip Motion (0-6.5s normal, 6.8s-9.5s reactive tracking jerk towards anomaly)
            frame = self._apply_reactive_camera_tracking(
                frame, frame_idx, total_frames, current_time_sec, tx, ty, camera_mode
            )

            # 4. Subtle chromatic glitch right at the startle reaction (7.4s - 8.2s)
            if 7.3 <= current_time_sec <= 8.1:
                frame = self._apply_subtle_glitch(frame, intensity=random.randint(2, 6))

            # 5. Apply Scanlines & Natural Analog Grain
            frame = (frame.astype(np.float32) * scanlines).astype(np.uint8)
            noise = np.random.randint(-8, 8, (self.height, self.width, 3), dtype=np.int16)
            frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

            # 6. Render Authentic HUD (NO BANNERS, NO RED CIRCLES, ONLY CAMERA DATA)
            frame = self._render_minimal_hud(
                frame,
                frame_idx,
                current_time_sec,
                camera_mode,
                hud_loc,
                hud_extra,
                start_time_base
            )

            process.stdin.write(frame.tobytes())

            if frame_idx % 90 == 0:
                pct = (frame_idx / total_frames) * 100
                print(f"[VIDEO ENGINE] Progress: {pct:.1f}% ({frame_idx}/{total_frames} frames)")

        if cap is not None:
            cap.release()

        process.stdin.close()
        process.wait()

        print(f"[VIDEO ENGINE] Rendering complete! Output: {output_video_path}")
        return output_video_path

    def _crop_to_vertical(self, frame: np.ndarray) -> np.ndarray:
        """Crops landscape or square footage to 9:16 vertical ratio (1080x1920)."""
        fh, fw = frame.shape[:2]
        target_aspect = self.width / float(self.height)  # 1080 / 1920 = 0.5625
        current_aspect = fw / float(fh)

        if current_aspect > target_aspect:
            # Wider than 9:16: Crop sides
            crop_w = int(fh * target_aspect)
            start_x = max(0, (fw - crop_w) // 2)
            cropped = frame[:, start_x:start_x + crop_w]
        else:
            # Taller than 9:16: Crop top/bottom
            crop_h = int(fw / target_aspect)
            start_y = max(0, (fh - crop_h) // 2)
            cropped = frame[start_y:start_y + crop_h, :]

        return cv2.resize(cropped, (self.width, self.height), interpolation=cv2.INTER_LINEAR)

    def _inject_dynamic_anomaly(
        self,
        frame: np.ndarray,
        t_sec: float,
        tx: int,
        ty: int,
        tr: int,
        camera_mode: str
    ) -> np.ndarray:
        """
        Injects a physical moving 50/50 anomaly between 6.8s and 10.2s.
        - Before 6.8s: completely untouched.
        - 6.8s - 10.2s: Organic silhouette creeps/steps across the scene with feathered alpha.
        - After 10.2s: Anomaly has ducked back into darkness, leaving scene empty.
        """
        if t_sec < 6.8 or t_sec > 10.2:
            return frame

        # Climax progression (0.0 to 1.0 over 3.4 seconds)
        duration_climax = 3.4
        progress = (t_sec - 6.8) / duration_climax
        
        # Smooth alpha envelope: peaks at 7.8s (midpoint)
        alpha_env = math.sin(progress * math.pi)
        base_alpha = float(np.clip(alpha_env * 0.65, 0.0, 0.65))

        h, w = frame.shape[:2]

        # Trajectory movement (moves 45px across 3.4s)
        cur_tx = int(tx + (45 * progress))
        cur_ty = int(ty + (12 * math.sin(progress * math.pi)))

        if camera_mode == "TRAIL_CAM":
            # Trail Cam: Infrared reflective tapetum lucidum eyes in the dark bushes
            return self._render_trailcam_eyes(frame, cur_tx, cur_ty, base_alpha, progress)

        # For DASHCAM, BODYCAM, CCTV: Organic shadowy humanoid/creature silhouette
        patch_r = max(40, int(tr * 1.4))
        x1 = max(0, cur_tx - patch_r)
        y1 = max(0, cur_ty - patch_r * 2)
        x2 = min(w, cur_tx + patch_r)
        y2 = min(h, cur_ty + patch_r)

        if x2 <= x1 or y2 <= y1:
            return frame

        pw = x2 - x1
        ph = y2 - y1

        # Generate organic silhouette mask (head + torso / creature crouch)
        mask = np.zeros((ph, pw), dtype=np.float32)
        center_x = pw // 2
        # Head
        cv2.circle(mask, (center_x, int(ph * 0.28)), int(pw * 0.22), 1.0, -1)
        # Torso / Shoulders
        cv2.ellipse(mask, (center_x, int(ph * 0.65)), (int(pw * 0.38), int(ph * 0.32)), 0, 0, 360, 1.0, -1)
        
        # Feather mask heavily (Gaussian blur radius 25px) to create natural 50/50 shadow blend
        ksize = max(15, (int(pw * 0.3) // 2) * 2 + 1)
        mask = cv2.GaussianBlur(mask, (ksize, ksize), 0)

        # Modulate by scene luminance (shadow is darker in light areas, blends in dark areas)
        sub_frame = frame[y1:y2, x1:x2].astype(np.float32)
        gray_sub = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        # Blend: darken the frame under the silhouette mask
        shadow_mult = 1.0 - (mask * base_alpha * 0.85)
        for c in range(3):
            sub_frame[:, :, c] = sub_frame[:, :, c] * shadow_mult

        frame[y1:y2, x1:x2] = np.clip(sub_frame, 0, 255).astype(np.uint8)
        return frame

    def _render_trailcam_eyes(
        self,
        frame: np.ndarray,
        cx: int,
        cy: int,
        alpha: float,
        progress: float
    ) -> np.ndarray:
        """Trail Cam: Eerie infrared eye shine reflection in the deep forest."""
        h, w = frame.shape[:2]
        eye_spacing = 24
        eye_y = cy
        eye1_x = cx - eye_spacing // 2
        eye2_x = cx + eye_spacing // 2

        # Blink once at 7.6s (progress around 0.24)
        if 0.22 <= progress <= 0.28:
            alpha = alpha * 0.1

        overlay = frame.copy()
        cv2.circle(overlay, (eye1_x, eye_y), 5, (230, 255, 230), -1)
        cv2.circle(overlay, (eye2_x, eye_y), 5, (230, 255, 230), -1)
        # Soft outer glow
        cv2.circle(overlay, (eye1_x, eye_y), 12, (180, 240, 180), -1)
        cv2.circle(overlay, (eye2_x, eye_y), 12, (180, 240, 180), -1)

        return cv2.addWeighted(overlay, alpha * 0.9, frame, 1.0 - (alpha * 0.9), 0)

    def _apply_reactive_camera_tracking(
        self,
        frame: np.ndarray,
        frame_idx: int,
        total_frames: int,
        t_sec: float,
        tx: int,
        ty: int,
        camera_mode: str
    ) -> np.ndarray:
        """
        0.0s - 6.8s: Natural footage motion.
        6.8s - 9.8s: Reactive tracking jerk / zoom-in towards target as movement is spotted!
        9.8s - 24.0s: Tense lingering focus with subtle breathing shake.
        """
        if camera_mode == "BODYCAM":
            base_dx = 5 * math.sin(t_sec * 3.8)
            base_dy = 7 * abs(math.sin(t_sec * 3.8))
            base_rot = 0.4 * math.sin(t_sec * 2.8)
        elif camera_mode == "DASHCAM":
            base_dx = random.uniform(-1.5, 1.5)
            base_dy = random.uniform(-1.5, 1.5)
            base_rot = random.uniform(-0.08, 0.08)
        else:
            # CCTV / Trail Cam
            base_dx = 1.5 * math.sin(t_sec * 0.5)
            base_dy = 1.5 * math.cos(t_sec * 0.4)
            base_rot = 0.04 * math.sin(t_sec * 0.2)

        # Reactive Tracking Phase
        if t_sec < 6.8:
            zoom = 1.0 + (0.015 * (t_sec / 6.8))
            cx = self.width / 2
            cy = self.height / 2
            dx = base_dx
            dy = base_dy
            rot = base_rot

        elif 6.8 <= t_sec <= 9.8:
            track_prog = (t_sec - 6.8) / 3.0
            smooth_track = 0.5 - 0.5 * math.cos(track_prog * math.pi)

            # Zoom smoothly increases to 1.18x
            zoom = 1.015 + (0.165 * smooth_track)

            cx = (self.width / 2) * (1.0 - smooth_track * 0.6) + (tx * smooth_track * 0.6)
            cy = (self.height / 2) * (1.0 - smooth_track * 0.6) + (ty * smooth_track * 0.6)

            # Reactive startled camera jerk at 7.4s - 8.0s
            if 7.3 <= t_sec <= 8.0:
                jerk = math.sin((t_sec - 7.3) * 22) * 12
                dx = base_dx + jerk
                dy = base_dy + abs(jerk)
                rot = base_rot + (jerk * 0.06)
            else:
                dx = base_dx
                dy = base_dy
                rot = base_rot
        else:
            # Aftermath: Locked on target area
            zoom = 1.18
            cx = (self.width / 2) * 0.4 + (tx * 0.6)
            cy = (self.height / 2) * 0.4 + (ty * 0.6)
            dx = base_dx * 0.4
            dy = base_dy * 0.4
            rot = base_rot * 0.3

        M = cv2.getRotationMatrix2D((cx, cy), rot, zoom)
        M[0, 2] += dx
        M[1, 2] += dy

        transformed = cv2.warpAffine(
            frame,
            M,
            (self.width, self.height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101
        )
        return transformed

    def _apply_subtle_glitch(self, frame: np.ndarray, intensity: int = 4) -> np.ndarray:
        """Brief, authentic sensor glitch when camera whips."""
        b, g, r = cv2.split(frame)
        h, w = frame.shape[:2]

        M_r = np.float32([[1, 0, intensity], [0, 1, 0]])
        M_b = np.float32([[1, 0, -intensity], [0, 1, 0]])

        r_shifted = cv2.warpAffine(r, M_r, (w, h), borderMode=cv2.BORDER_REFLECT)
        b_shifted = cv2.warpAffine(b, M_b, (w, h), borderMode=cv2.BORDER_REFLECT)

        return cv2.merge([b_shifted, g, r_shifted])

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
        """
        Pure, authentic camera HUD only.
        NO banners, NO artificial warning text, NO emojis.
        """
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # 1. Blinking REC Indicator [● REC]
        rec_blink = (int(t_sec * 2) % 2) == 0
        rec_color = (255, 30, 30) if rec_blink else (140, 140, 140)
        draw.text((60, 80), "● REC", font=self.font_clock, fill=rec_color)

        # 2. Top-Right Mode / Telemetry
        draw.text((self.width - 450, 80), hud_extra, font=self.font_hud, fill=(210, 210, 210))

        # 3. Bottom HUD: Running Millisecond Digital Timestamp
        millis = int((frame_idx % self.fps) * (1000 / self.fps))
        clock_str = f"2026-10-24 03:14:{int(22 + t_sec):02d}.{millis:03d}"
        draw.text((60, self.height - 140), clock_str, font=self.font_clock, fill=(235, 235, 235))
        draw.text((60, self.height - 90), f"{hud_loc} | {camera_mode}", font=self.font_hud, fill=(175, 175, 175))

        # 4. Mode-specific telemetry
        if camera_mode == "DASHCAM":
            speed = 48 + int(math.sin(t_sec * 0.7) * 3)
            draw.text((self.width - 380, self.height - 140), f"SPEED: {speed} MPH", font=self.font_hud, fill=(235, 235, 235))
            draw.text((self.width - 380, self.height - 90), "GPS: 34.05°N 118.24°W", font=self.font_hud, fill=(175, 175, 175))
        elif camera_mode == "TRAIL_CAM":
            draw.text((self.width - 380, self.height - 140), "TEMP: 44°F / 7°C", font=self.font_hud, fill=(120, 240, 120))
            draw.text((self.width - 380, self.height - 90), "PIR MOTION: ACTIVE", font=self.font_hud, fill=(120, 240, 120))
        elif camera_mode == "BODYCAM":
            draw.text((self.width - 400, self.height - 140), "AXON BODY 3", font=self.font_hud, fill=(235, 235, 235))
            draw.text((self.width - 400, self.height - 90), "AUDIO ON [MIC]", font=self.font_hud, fill=(175, 175, 175))

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def _get_audio_duration(self, audio_path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return float(res.stdout.strip())
        except Exception:
            return 24.0
