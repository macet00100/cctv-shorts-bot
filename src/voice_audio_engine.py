import time
from pathlib import Path
from typing import Dict, Any

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

from src.config import OUTPUT_DIR

class AuthenticCameraAudioEngine:
    """
    Hyper-Realistic Incident Camera Microphone & Foley Sound Engine.
    NO AI voiceover, NO artificial music.
    Generates authentic near-microphone foley for real-life close calls and accidents:
    - CCTV: City street ambience, pedestrian footsteps, sudden falling whoosh, loud ceramic smash, crowd gasp.
    - DASHCAM: Cabin acoustic, road tire rumble, sudden screeching ABS brake skid, sharp horn honk.
    - DOORBELL_CAM: Porch wind, footsteps on wood, ice slide squeak, cardboard box thud, embarrassed chuckle.
    - BODYCAM: Action breathing, rushing wind, sudden warning shout, reflex catch clatter.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.output_dir = OUTPUT_DIR

    def build_audio(self, scenario: Dict[str, Any], duration: float = 24.0) -> Path:
        camera_mode = scenario.get("camera_mode", "CCTV")
        incident_type = scenario.get("anomaly_type") or scenario.get("incident_type", "HEROIC_CLOSE_CALL")
        print(f"[AUDIO ENGINE] Synthesizing incident foley for [{camera_mode} | {incident_type}] (Duration: {duration:.1f}s)...")

        total_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, total_samples, endpoint=False)
        track = np.zeros(total_samples, dtype=np.float32)

        if camera_mode == "DASHCAM":
            track = self._build_dashcam_incident(t, total_samples, duration, incident_type)
        elif camera_mode == "DOORBELL_CAM":
            track = self._build_doorbell_incident(t, total_samples, duration, incident_type)
        elif camera_mode == "BODYCAM":
            track = self._build_bodycam_incident(t, total_samples, duration, incident_type)
        else:
            # CCTV
            track = self._build_cctv_incident(t, total_samples, duration, incident_type)

        # Soft limiter
        peak = np.max(np.abs(track))
        if peak > 0.95:
            track = track / peak * 0.95

        master_int16 = (track * 32767.0).astype(np.int16)
        master_wav = self.output_dir / f"foley_{camera_mode}_{int(time.time())}.wav"
        wavfile.write(str(master_wav), self.sample_rate, master_int16)

        print(f"[AUDIO ENGINE] Incident mic track compiled: {master_wav.name}")
        return master_wav

    def _build_cctv_incident(self, t: np.ndarray, total_samples: int, duration: float, incident: str) -> np.ndarray:
        """CCTV: Street ambiance, footsteps, falling whoosh, heavy ceramic crash, crowd gasp."""
        track = np.zeros(total_samples, dtype=np.float32)

        # 1. City Street Ambience & Traffic Rumble
        white_noise = np.random.uniform(-1, 1, total_samples).astype(np.float32)
        b, a = butter(2, [40 / (0.5 * self.sample_rate), 350 / (0.5 * self.sample_rate)], btype='band')
        traffic_rumble = lfilter(b, a, white_noise) * 0.25
        track += traffic_rumble

        # Subtle 50Hz electrical microphone hum
        track += 0.08 * np.sin(2 * np.pi * 50 * t)

        # 2. Footsteps on sidewalk
        for step_sec in np.arange(0.5, 6.8, 0.65):
            idx = int(step_sec * self.sample_rate)
            slen = int(0.12 * self.sample_rate)
            if idx + slen < total_samples:
                ts = np.linspace(0, 0.12, slen)
                thud = np.sin(2 * np.pi * 90 * ts) * np.exp(-ts * 35.0) * 0.18
                track[idx:idx + slen] += thud

        # 3. High-Pitched Falling Object Whoosh (6.8s - 7.5s)
        whoosh_idx = int(6.8 * self.sample_rate)
        whoosh_len = int(0.7 * self.sample_rate)
        if whoosh_idx + whoosh_len < total_samples:
            tw = np.linspace(0, 0.7, whoosh_len)
            whoosh_freq = 1200 - 800 * tw
            whoosh = np.sin(2 * np.pi * whoosh_freq * tw) * np.exp(-abs(tw - 0.5) * 5) * 0.22
            track[whoosh_idx:whoosh_idx + whoosh_len] += whoosh

        # 4. Sudden Bystander Gasp / Shout (7.4s)
        gasp_idx = int(7.3 * self.sample_rate)
        gasp_len = int(0.6 * self.sample_rate)
        if gasp_idx + gasp_len < total_samples:
            tg = np.linspace(0, 0.6, gasp_len)
            gasp = np.random.uniform(-0.5, 0.5, gasp_len) * np.sin(np.pi * tg / 0.6) * np.exp(-tg * 2.5) * 0.35
            track[gasp_idx:gasp_idx + gasp_len] += gasp

        # 5. Heavy Ceramic Smashed / Impact Thud (7.55s)
        crash_idx = int(7.55 * self.sample_rate)
        crash_len = int(1.4 * self.sample_rate)
        if crash_idx + crash_len < total_samples:
            tc = np.linspace(0, 1.4, crash_len)
            # Low frequency heavy thud
            thud = np.sin(2 * np.pi * 65 * tc) * np.exp(-tc * 14.0) * 0.75
            # High frequency ceramic glass shatter
            shatter_noise = np.random.uniform(-1, 1, crash_len).astype(np.float32)
            b_shat, a_shat = butter(2, [1800 / (0.5 * self.sample_rate), 8000 / (0.5 * self.sample_rate)], btype='band')
            filtered_shatter = lfilter(b_shat, a_shat, shatter_noise) * np.exp(-tc * 8.0) * 0.65
            track[crash_idx:crash_idx + crash_len] += (thud + filtered_shatter)

        # 6. Crowd relief chatter / murmur (8.8s - 14.0s)
        murmur_idx = int(8.8 * self.sample_rate)
        murmur_len = int(5.0 * self.sample_rate)
        if murmur_idx + murmur_len < total_samples:
            tm = np.linspace(0, 5.0, murmur_len)
            b_mur, a_mur = butter(2, [250 / (0.5 * self.sample_rate), 1400 / (0.5 * self.sample_rate)], btype='band')
            murmur = lfilter(b_mur, a_mur, np.random.uniform(-0.3, 0.3, murmur_len).astype(np.float32)) * 0.15
            track[murmur_idx:murmur_idx + murmur_len] += murmur

        return track

    def _build_dashcam_incident(self, t: np.ndarray, total_samples: int, duration: float, incident: str) -> np.ndarray:
        """DASHCAM: Engine rumble, tire roll, screeching ABS brakes at 7.2s, sharp horn, driver gasp."""
        track = np.zeros(total_samples, dtype=np.float32)

        # 1. Car Engine & Cabin Rumble
        engine = 0.20 * np.sin(2 * np.pi * 32 * t) + 0.10 * np.sin(2 * np.pi * 64 * t)
        noise = np.random.uniform(-0.15, 0.15, total_samples).astype(np.float32)
        b, a = butter(2, [80 / (0.5 * self.sample_rate), 600 / (0.5 * self.sample_rate)], btype='band')
        road_friction = lfilter(b, a, noise) * 0.35
        track += (engine + road_friction)

        # 2. Screeching ABS Tire Skid (7.2s - 8.2s)
        skid_idx = int(7.2 * self.sample_rate)
        skid_len = int(1.1 * self.sample_rate)
        if skid_idx + skid_len < total_samples:
            ts = np.linspace(0, 1.1, skid_len)
            skid_noise = np.random.uniform(-1, 1, skid_len).astype(np.float32)
            b_skid, a_skid = butter(2, [2200 / (0.5 * self.sample_rate), 5000 / (0.5 * self.sample_rate)], btype='band')
            skid = lfilter(b_skid, a_skid, skid_noise) * np.sin(np.pi * ts / 1.1) * 0.70
            track[skid_idx:skid_idx + skid_len] += skid

        # 3. Sudden Emergency Horn Honk (7.4s - 7.9s)
        horn_idx = int(7.4 * self.sample_rate)
        horn_len = int(0.5 * self.sample_rate)
        if horn_idx + horn_len < total_samples:
            th = np.linspace(0, 0.5, horn_len)
            horn = (np.sin(2 * np.pi * 440 * th) * 0.4 + np.sin(2 * np.pi * 554 * th) * 0.3) * np.exp(-th * 2.0)
            track[horn_idx:horn_idx + horn_len] += horn

        # 4. Driver Startle Exhale (8.4s)
        sigh_idx = int(8.4 * self.sample_rate)
        sigh_len = int(0.8 * self.sample_rate)
        if sigh_idx + sigh_len < total_samples:
            tg = np.linspace(0, 0.8, sigh_len)
            b_g, a_g = butter(2, [150 / (0.5 * self.sample_rate), 900 / (0.5 * self.sample_rate)], btype='band')
            sigh = lfilter(b_g, a_g, np.random.uniform(-0.4, 0.4, sigh_len).astype(np.float32)) * np.exp(-tg * 2.2) * 0.3
            track[sigh_idx:sigh_idx + sigh_len] += sigh

        return track

    def _build_doorbell_incident(self, t: np.ndarray, total_samples: int, duration: float, incident: str) -> np.ndarray:
        """DOORBELL_CAM: Outdoor porch breeze, shoe slide on ice, cardboard thud, laugh."""
        track = np.zeros(total_samples, dtype=np.float32)

        # Ambient gentle wind
        noise = np.random.uniform(-0.15, 0.15, total_samples).astype(np.float32)
        b, a = butter(2, [60 / (0.5 * self.sample_rate), 400 / (0.5 * self.sample_rate)], btype='band')
        track += lfilter(b, a, noise) * 0.25

        # Footsteps approaching porch
        for step_sec in np.arange(1.0, 6.5, 0.8):
            idx = int(step_sec * self.sample_rate)
            slen = int(0.15 * self.sample_rate)
            if idx + slen < total_samples:
                ts = np.linspace(0, 0.15, slen)
                thud = np.sin(2 * np.pi * 120 * ts) * np.exp(-ts * 28.0) * 0.25
                track[idx:idx + slen] += thud

        # Slip squeak on ice / smooth surface (7.1s)
        slip_idx = int(7.1 * self.sample_rate)
        slip_len = int(0.35 * self.sample_rate)
        if slip_idx + slip_len < total_samples:
            tsl = np.linspace(0, 0.35, slip_len)
            chirp = np.sin(2 * np.pi * (800 + 1400 * tsl) * tsl) * np.exp(-tsl * 8.0) * 0.45
            track[slip_idx:slip_idx + slip_len] += chirp

        # Padded thud on ground (7.5s)
        thud_idx = int(7.5 * self.sample_rate)
        thud_len = int(0.5 * self.sample_rate)
        if thud_idx + thud_len < total_samples:
            tt = np.linspace(0, 0.5, thud_len)
            thud = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 12.0) * 0.60
            track[thud_idx:thud_idx + thud_len] += thud

        # Wholesome chuckle at 8.6s
        chuckle_idx = int(8.6 * self.sample_rate)
        chuckle_len = int(1.2 * self.sample_rate)
        if chuckle_idx + chuckle_len < total_samples:
            tch = np.linspace(0, 1.2, chuckle_len)
            track[chuckle_idx:chuckle_idx + chuckle_len] += np.random.uniform(-0.15, 0.15, chuckle_len) * np.sin(np.pi * tch / 1.2) * 0.2

        return track

    def _build_bodycam_incident(self, t: np.ndarray, total_samples: int, duration: float, incident: str) -> np.ndarray:
        """BODYCAM: Action breathing, rushing wind, sudden shout, reflex catch clatter."""
        track = np.zeros(total_samples, dtype=np.float32)

        # Courier / bike rushing air
        noise = np.random.uniform(-0.25, 0.25, total_samples).astype(np.float32)
        b, a = butter(2, [120 / (0.5 * self.sample_rate), 800 / (0.5 * self.sample_rate)], btype='band')
        track += lfilter(b, a, noise) * 0.35

        # Tactical/action breathing
        for breath_sec in np.arange(0.5, duration - 1.0, 2.2):
            idx = int(breath_sec * self.sample_rate)
            blen = int(1.0 * self.sample_rate)
            if idx + blen < total_samples:
                tb = np.linspace(0, 1.0, blen)
                breath = np.sin(np.pi * tb / 1.0) * np.random.uniform(-0.2, 0.2, blen) * 0.3
                track[idx:idx + blen] += breath

        # Action gasp / reflex catch clatter at 7.5s
        clatter_idx = int(7.4 * self.sample_rate)
        clatter_len = int(0.6 * self.sample_rate)
        if clatter_idx + clatter_len < total_samples:
            tc = np.linspace(0, 0.6, clatter_len)
            thud = np.sin(2 * np.pi * 140 * tc) * np.exp(-tc * 16.0) * 0.55
            track[clatter_idx:clatter_idx + clatter_len] += thud

        return track
