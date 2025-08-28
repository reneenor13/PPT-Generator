import json
import asyncio
from typing import Dict, List, Any
import openai
import anthropic
import google.generativeai as genai
from openai import OpenAI
import httpx

class LLMClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider.lower()
        self.api_key = api_key
        self._setup_client()
    
    def _setup_client(self):
        if self.provider == "openai":
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "gemini":
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-pro')
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def generate_slide_structure(self, text: str, guidance: str = "") -> Dict[str, Any]:
        prompt = self._create_prompt(text, guidance)
        
        try:
            if self.provider == "openai":
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt)
            elif self.provider == "gemini":
                response = await self._call_gemini(prompt)
            
            return self._parse_response(response)
        
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")
    
    def _create_prompt(self, text: str, guidance: str) -> str:
        base_prompt = f"""
        Analyze the following text and create a structured presentation outline.
        
        Text to analyze:
        {text}
        
        Additional guidance: {guidance if guidance else "Create a professional presentation"}
        
        Please respond with ONLY a valid JSON object with this exact structure:
        {{
            "title": "Presentation Title",
            "slides": [
                {{
                    "title": "Slide Title",
                    "content": "Main content points as bullet points",
                    "speaker_notes": "Detailed speaker notes"
                }}
            ]
        }}
        
        Guidelines:
        - Create 5-12 slides based on content length
        - Each slide should have clear, concise content
        - Include speaker notes for each slide
        - Ensure logical flow between slides
        - Make the first slide a title slide
        - Include a conclusion slide if appropriate
        """
        return base_prompt
    
    async def _call_openai(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str) -> str:
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def _call_gemini(self, prompt: str) -> str:
        response = await self.client.generate_content_async(prompt)
        return response.text
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            # Clean up the response to extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            parsed = json.loads(response)
            
            # Validate structure
            if not isinstance(parsed, dict) or "slides" not in parsed:
                raise ValueError("Invalid response structure")
            
            return parsed
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
