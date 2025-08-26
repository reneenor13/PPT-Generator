import os
from typing import List
from google.generativeai import Client as GoogleClient
import requests

class LLMClient:
    def __init__(self, provider: str, api_key: str = None):
        self.provider = provider.lower()

        if self.provider == "google":
            if not api_key:
                raise ValueError("Google API key is required")
            self.client = GoogleClient(api_key=api_key)

        elif self.provider == "gemini":
            # Gemini key will come from environment if not provided
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("Gemini API key not found in environment")
        else:
            raise NotImplementedError(f"Provider {self.provider} not supported.")

    def generate_slide_outline(self, text: str, guidance: str = "") -> List[str]:
        prompt = f"Split the following text into slide-wise points:\n{text}\nGuidance: {guidance}"

        if self.provider == "google":
            response = self.client.chat(
                model="chat-bison-001",
                messages=[{"author": "user", "content": prompt}],
                temperature=0.5,
                max_output_tokens=800
            )
            slides = response.last.split("\n\n")

        elif self.provider == "gemini":
            url = "https://api.gemini.com/v1/generate"  # Replace with actual endpoint
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {"prompt": prompt, "model": "gemini-1.5", "temperature": 0.5}
            r = requests.post(url, json=data, headers=headers)
            r.raise_for_status()
            slides_text = r.json().get("text", "")
            slides = slides_text.split("\n\n")

        return [s.strip() for s in slides if s.strip()]
