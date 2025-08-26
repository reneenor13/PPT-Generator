import openai
from typing import List

class LLMClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider.lower()
        self.api_key = api_key
        if self.provider == "openai":
            openai.api_key = api_key
        else:
            raise NotImplementedError(f"{self.provider} not supported yet.")

    def generate_slide_outline(self, text: str, guidance: str = "") -> List[str]:
        """
        Returns a list of slides (title + content)
        """
        prompt = f"Split the following text into slide-wise points:\n{text}\nGuidance: {guidance}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        slides = response['choices'][0]['message']['content'].split("\n\n")
        return [s.strip() for s in slides if s.strip()]
