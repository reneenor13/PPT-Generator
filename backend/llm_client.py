import requests

def get_slide_outline(text, guidance, api_key):
    prompt = f"""
    Turn the following text into a slide deck outline.
    Guidance: {guidance}
    Respond in JSON: [{{"title": "...", "bullets": ["...", "..."]}}, ...]
    Text: {text}
    """

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    data = {"contents": [{"parts":[{"text": prompt}]}]}

    resp = requests.post(url, headers=headers, params=params, json=data)
    slides = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return eval(slides)  # Or json.loads after sanitization

