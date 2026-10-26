import os
import random
import time
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

import requests
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from src.config import OUTPUT_DIR, HF_TOKEN, VIDEO_WIDTH, VIDEO_HEIGHT

class FoundFootageImageGenerator:
    """
    Generates authentic, high-realism found footage frames using FLUX.1-schnell
    with multi-tier free fallbacks (Hugging Face Spaces -> HF Inference API -> Pollinations Flux).
    """

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.hf_token = HF_TOKEN

    def generate(self, scenario: Dict[str, Any]) -> Path:
        prompt = scenario.get("image_prompt", "")
        camera_mode = scenario.get("camera_mode", "CCTV")
        seed = random.randint(100000, 9999999)

        # Enhance prompt with surveillance realism keywords
        enhanced_prompt = self._refine_prompt(prompt, camera_mode)
        print(f"[IMAGE GENERATOR] Generating image for Mode: {camera_mode}...")
        print(f"[IMAGE GENERATOR] Prompt: {enhanced_prompt[:120]}... (seed={seed})")

        img_path = self.output_dir / f"frame_raw_{int(time.time())}.png"

        # Attempt 1: Fast Pollinations FLUX Engine (Free Tier, ~8s, no queue blocks)
        success = self._try_pollinations_flux(enhanced_prompt, seed, img_path)

        # Attempt 2: Hugging Face Gradio Client / Spaces fallback
        if not success:
            print("[IMAGE GENERATOR] Trying Hugging Face Spaces...")
            success = self._try_hf_gradio(enhanced_prompt, seed, img_path)

        # Attempt 3: Hugging Face Inference API
        if not success and self.hf_token:
            print("[IMAGE GENERATOR] Trying HF Inference API...")
            success = self._try_hf_inference_api(enhanced_prompt, seed, img_path)

        # Attempt 4: Synthetic procedural fallback if offline
        if not success:
            print("[IMAGE GENERATOR] Generating procedural dark surveillance fallback frame...")
            self._create_procedural_fallback(camera_mode, img_path)

        # Post-process image to apply camera mode specific optics
        processed_path = self._apply_camera_optics(img_path, camera_mode, scenario.get("red_circle_target"))
        return processed_path

    def _refine_prompt(self, base_prompt: str, camera_mode: str) -> str:
        mode_tags = {
            "CCTV": "Authentic security camera footage, high angle CCTV mount, grainy low-light security sensor, wide angle security lens, desaturated surveillance aesthetic, timestamp aesthetic, realistic 4k security detail",
            "BODYCAM": "Real police bodycam POV, Axon body 3 perspective, chest-mounted camera view, tactical flashlight beam piercing pitch black darkness, motion blur, gritty raw found footage, authentic handheld jitter",
            "DASHCAM": "Authentic car dashcam footage, view through vehicle windshield, car hood silhouette visible at bottom edge, headlights illuminating dark road, foggy night highway, realistic 1080p car recorder sensor",
            "TRAIL_CAM": "Authentic infrared trail camera photo, night vision game cam, black and white infrared IR sensor, high contrast flash in dark forest, wilderness surveillance, eerie reflective eyes glowing"
        }
        tag = mode_tags.get(camera_mode, mode_tags["CCTV"])
        return f"{base_prompt}, {tag}, ultra photorealistic, natural textures, analog noise, unedited documentary aesthetic, 9:16 aspect ratio"

    def _try_hf_gradio(self, prompt: str, seed: int, out_path: Path) -> bool:
        try:
            from gradio_client import Client
            # Try popular free FLUX.1-schnell spaces
            spaces = ["black-forest-labs/FLUX.1-schnell", "mrfakename/FLUX.1-schnell"]
            for space in spaces:
                try:
                    try:
                        client = Client(space, token=self.hf_token if self.hf_token else None)
                    except TypeError:
                        client = Client(space)
                    result = client.predict(
                        prompt=prompt,
                        seed=seed,
                        randomize_seed=False,
                        width=768,
                        height=1344,
                        num_inference_steps=4,
                        api_name="/infer"
                    )
                    # Result is a tuple where result[0] is the temporary image path
                    if isinstance(result, (tuple, list)) and len(result) > 0:
                        temp_file = result[0]
                        img = Image.open(temp_file).convert("RGB")
                        img.save(out_path, "PNG")
                        print(f"[IMAGE GENERATOR] Successfully generated via HF Space: {space}")
                        return True
                except Exception as inner_e:
                    print(f"[IMAGE GENERATOR] Space {space} failed: {inner_e}")
                    continue
        except Exception as e:
            print(f"[IMAGE GENERATOR] Gradio client error: {e}")
        return False

    def _try_hf_inference_api(self, prompt: str, seed: int, out_path: Path) -> bool:
        try:
            api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            payload = {
                "inputs": prompt,
                "parameters": {"width": 768, "height": 1344, "seed": seed}
            }
            resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                print("[IMAGE GENERATOR] Successfully generated via HF Inference API.")
                return True
            else:
                print(f"[IMAGE GENERATOR] HF API returned status {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"[IMAGE GENERATOR] HF Inference API error: {e}")
        return False

    def _try_pollinations_flux(self, prompt: str, seed: int, out_path: Path) -> bool:
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            # Pollinations free fast FLUX generator
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1344&model=flux&seed={seed}&nologo=true"
            resp = requests.get(url, timeout=90)
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                print("[IMAGE GENERATOR] Successfully generated via Pollinations FLUX Engine.")
                return True
            else:
                print(f"[IMAGE GENERATOR] Pollinations returned code {resp.status_code}")
        except Exception as e:
            print(f"[IMAGE GENERATOR] Pollinations error: {e}")
        return False

    def _create_procedural_fallback(self, camera_mode: str, out_path: Path):
        """Creates a dark, eerie procedural canvas if external APIs are unreachable."""
        arr = np.random.randint(5, 30, (VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
        # Create subtle gradient
        y_indices = np.linspace(0.8, 1.2, VIDEO_HEIGHT)[:, None, None]
        arr = np.clip(arr * y_indices, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        img.save(out_path, "PNG")

    def _apply_camera_optics(self, img_path: Path, camera_mode: str, target: Optional[list]) -> Path:
        """
        Post-processes the raw AI image to match authentic camera hardware optics:
        CCTV (fisheye & desaturated), BODYCAM (flashlight cone), TRAIL_CAM (IR green/monochrome).
        """
        img = Image.open(img_path).convert("RGB")
        # Resize/crop to 1080x1920
        img = ImageOps.fit(img, (VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)

        arr = np.array(img, dtype=np.float32)

        if camera_mode == "TRAIL_CAM":
            # Convert to monochrome IR with slight greenish-cyan tint
            gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            arr[:, :, 0] = gray * 0.85
            arr[:, :, 1] = gray * 1.05  # Slight night vision green
            arr[:, :, 2] = gray * 0.85
            arr = np.clip(arr * 1.2, 0, 255)

        elif camera_mode == "BODYCAM":
            # Add realistic tactical flashlight beam centered on middle/target
            h, w = VIDEO_HEIGHT, VIDEO_WIDTH
            tx = int(target[0] * w) if target else w // 2
            ty = int(target[1] * h) if target else int(h * 0.45)

            y_grid, x_grid = np.ogrid[:h, :w]
            dist_sq = (x_grid - tx) ** 2 + (y_grid - ty) ** 2
            max_dist_sq = (w * 0.5) ** 2 + (h * 0.5) ** 2

            # Spotlight falloff
            falloff = np.clip(1.0 - (dist_sq / (max_dist_sq * 0.85)), 0.15, 1.2)
            arr = arr * falloff[:, :, None]

        elif camera_mode == "CCTV":
            # Desaturate slightly, high contrast, subtle vignette
            h, w = VIDEO_HEIGHT, VIDEO_WIDTH
            gray = (arr.mean(axis=2, keepdims=True))
            arr = arr * 0.65 + gray * 0.35  # Desaturate
            # Vignette
            y_grid, x_grid = np.ogrid[:h, :w]
            center_x, center_y = w / 2, h / 2
            dist_from_center = np.sqrt((x_grid - center_x) ** 2 + (y_grid - center_y) ** 2)
            max_r = np.sqrt(center_x ** 2 + center_y ** 2)
            vignette = 1.0 - 0.45 * (dist_from_center / max_r) ** 2
            arr = arr * vignette[:, :, None]

        elif camera_mode == "DASHCAM":
            # Add dark silhouette on bottom 10% to represent car hood / dashboard
            h = VIDEO_HEIGHT
            hood_h = int(h * 0.08)
            arr[h - hood_h:, :, :] *= 0.25

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        final_img = Image.fromarray(arr)

        processed_path = self.output_dir / f"frame_optic_{camera_mode}_{int(time.time())}.png"
        final_img.save(processed_path, "PNG")
        return processed_path
