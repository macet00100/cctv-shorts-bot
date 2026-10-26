import os
import requests

key = os.getenv("KLING_API_KEY", "")
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

prompt = 'CCTV street sidewalk security camera footage'
models = ['kling-v3', 'kling-v3-std', 'kling-v3-pro', 'kling-v2-standard', 'kling-v2-std', 'kling-v2-pro']

for m in models:
    payload = {
        'model_name': m,
        'prompt': prompt,
        'duration': '5',
        'aspect_ratio': '9:16'
    }
    r = requests.post('https://api.klingai.com/v1/videos/text2video', json=payload, headers=headers)
    res = r.json()
    print(f"model_name={m} -> code={res.get('code')}, msg={res.get('message')}")
