import os
from pathlib import Path

# Load local .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
AUDIO_DIR = ASSETS_DIR / "audio"
OUTPUT_DIR = BASE_DIR / "output"
MUSE_DATA_DIR = BASE_DIR / "muse_browser_data"
HISTORY_FILE = BASE_DIR / "history_cctv_posts.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MUSE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Video Generation Engine Selection (MUSE, WAN, KLING)
VIDEO_PROVIDER = os.getenv("VIDEO_PROVIDER", "MUSE").upper()

# API Keys & Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# YouTube Credentials
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

# Facebook Credentials
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")

# Webhook for monitoring (Discord, Telegram, or cron-job.org callback)
NOTIFICATION_WEBHOOK = os.getenv("NOTIFICATION_WEBHOOK", "")

# 3-Axis Matrix Definitions (120 Unique Combinations)
# Niche: Real-Life Incidents, Close Calls, Heroic Saves & Funny Fails (100% Non-Violent)
CAMERA_MODES = [
    "CCTV",           # Street surveillance, shopfront, building corner
    "DASHCAM",        # Car windshield POV, intersection, highway
    "DOORBELL_CAM",   # Smart doorbell camera, front porch, driveway
    "BODYCAM"         # Delivery courier, bike rider, patrol officer POV
]

LOCATIONS = [
    "CITY_SIDEWALK",         # Busy pedestrian street outside high-rise building
    "BUSY_INTERSECTION",     # Traffic crosswalk, zebra crossing, street corner
    "RESIDENTIAL_PORCH",     # Front porch doorstep, icy pathway, driveway
    "CONVENIENCE_STORE",     # Grocery store aisles, glass door entrance
    "GAS_STATION_LOT",       # Fuel pump area, parking space, car wash exit
    "CONSTRUCTION_PERIMETER" # Scaffolding walkway, work zone boundary
]

INCIDENTS = [
    "HEROIC_CLOSE_CALL",     # Falling flowerpot/tile/sign, hero pushes pedestrian away in nick of time
    "FUNNY_SLIP_TUMBLE",     # Slipping on icy porch/wet floor, comical cartoonish stumble, safe recovery
    "TRAFFIC_NEAR_MISS",     # Sudden emergency braking 2 inches from bumper, runaway stroller saved
    "MIRACLE_CATCH_REFLEX",  # Reflex catch of falling item, sliding object deflected before impact
    "RUNAWAY_OBJECT_CHAOS"   # Rogue tire rolling down road, runaway shopping cart hitting soft barrier
]
ANOMALIES = INCIDENTS  # Backward compatibility alias

# Video Specifications
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
TARGET_DURATION = 24.0  # seconds (Full 20-30s found footage with real motion & 50/50 climax)

# Pexels Video API (Free 100%, 20,000 req/mo)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Fonts
MONO_FONT_PATH = FONTS_DIR / "ShareTechMono-Regular.ttf"

# Voice Configuration per Camera Mode
VOICE_MAPPING = {
    "CCTV": "en-US-GuyNeural",
    "BODYCAM": "en-US-AndrewNeural",
    "DASHCAM": "en-US-BrianNeural",
    "TRAIL_CAM": "en-US-ChristopherNeural"
}
