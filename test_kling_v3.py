import os
import requests

key = os.getenv("KLING_API_KEY", "")
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

prompt = 'CCTV street sidewalk security camera footage'
candidates = [
    'kling-v3', 'kling-v3-0', 'kling-v3.0',
    'kling-v4', 'kling-v4-0', 'kling-v4.0',
    'kling-v2-0', 'kling-v2-2', 'kling-v2.2',
    'kling-3', 'kling-4', 'kling-omni', 'kling-omni-v1',
    'kling-v1-plus', 'kling-v1.5-pro'
]

for m in candidates:
    payload = {
        'model_name': m,
        'prompt': prompt,
        'duration': '5',
        'aspect_ratio': '9:16'
    }
    r = requests.post('https://api.klingai.com/v1/videos/text2video', json=payload, headers=headers)
    res = r.json()
    code = res.get('code')
    msg = res.get('message')
    print(f"model_name={m} -> code={code}, msg={msg}")
    if code == 0:
        print("FOUND ACTIVE MODEL:", m, res)
        break
