from google.generativeai import Client
from typing import List

class LLMClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider.lower()
        if self.provider != "google":
            raise NotImplementedError(f"{self.provider} not supported yet.")
        self.client = Client(api_key=api_key)

    def generate_slide_outline(self, text: str, guidance: str = "") -> List[str]:
        """
        Generates slide content using Google Generative AI.
        Returns a list of slides (title + content)
        """
        prompt = f"Split the following text into slide-wise points:\n{text}\nGuidance: {guidance}"

        response = self.client.chat(
            model="chat-bison-001",
            messages=[{"author": "user", "content": prompt}],
            temperature=0.5,
            max_output_tokens=800
        )

        slides = response.last.split("\n\n")  # Split by double newline for slide separation
        return [s.strip() for s in slides if s.strip()]
