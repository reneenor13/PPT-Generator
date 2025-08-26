import openai
import anthropic
import google.generativeai as genai
import json
import re

class LLMClient:
    def __init__(self, provider, api_key):
        self.provider = provider.lower()
        self.api_key = api_key
        self._setup_client()
    
    def _setup_client(self):
        if self.provider == 'openai':
            openai.api_key = self.api_key
        elif self.provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == 'google':
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_slide_structure(self, text_content, guidance=''):
        prompt = self._create_prompt(text_content, guidance)
        
        try:
            if self.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                return self._parse_response(response.choices[0].message.content)
            
            elif self.provider == 'anthropic':
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return self._parse_response(response.content[0].text)
            
            elif self.provider == 'google':
                response = self.model.generate_content(prompt)
                return self._parse_response(response.text)
                
        except Exception as e:
            raise Exception(f"LLM API error: {str(e)}")
    
    def _create_prompt(self, text_content, guidance):
        base_prompt = f"""
        Analyze the following text and create a structured presentation outline.
        
        Text Content:
        {text_content}
        
        Additional Guidance: {guidance if guidance else 'Create a professional presentation'}
        
        Please provide a JSON response with the following structure:
        {{
            "title": "Presentation Title",
            "slides": [
                {{
                    "title": "Slide Title",
                    "content": ["Bullet point 1", "Bullet point 2", "Bullet point 3"],
                    "type": "content" // or "title", "conclusion"
                }}
            ]
        }}
        
        Rules:
        - Create 5-12 slides based on content length
        - Extract key points and organize logically
        - Include title slide and conclusion slide
        - Make content concise and presentation-friendly
        """
        return base_prompt
    
    def _parse_response(self, response_text):
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in response")
        except (json.JSONDecodeError, ValueError):
            # Fallback parsing
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text):
        # Simple fallback if JSON parsing fails
        lines = text.split('\n')
        slides = []
        current_slide = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or line.startswith('Slide'):
                if current_slide:
                    slides.append(current_slide)
                current_slide = {
                    "title": line.replace('#', '').replace('Slide', '').strip(),
                    "content": [],
                    "type": "content"
                }
            elif line.startswith('-') or line.startswith('*'):
                if current_slide:
                    current_slide["content"].append(line[1:].strip())
        
        if current_slide:
            slides.append(current_slide)
        
        return {
            "title": "Generated Presentation",
            "slides": slides
        }
