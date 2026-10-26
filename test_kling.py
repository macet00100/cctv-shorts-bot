import os
import requests

key = os.getenv("KLING_API_KEY", "")
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

prompt = 'CCTV street sidewalk security camera footage'
candidates = ['kling-v2.6-std', 'kling-v2.6-pro', 'kling-v2.5-turbo', 'kling-3.0', 'kling-v2.1', 'kling-v2-1-master', 'kling-video-o1']

for m in candidates:
    # Test with "model_name"
    payload = {
        'model_name': m,
        'prompt': prompt,
        'duration': '5',
        'aspect_ratio': '9:16'
    }
    r = requests.post('https://api.klingai.com/v1/videos/text2video', json=payload, headers=headers)
    print(f"model_name={m} -> {r.status_code} : {r.text[:120]}")

    # Test with "model"
    payload2 = {
        'model': m,
        'prompt': prompt,
        'duration': '5',
        'aspect_ratio': '9:16'
    }
    r2 = requests.post('https://api.klingai.com/v1/videos/text2video', json=payload2, headers=headers)
    print(f"model={m} -> {r2.status_code} : {r2.text[:120]}")
