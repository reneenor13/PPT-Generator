import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import re

import openai
import anthropic
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified client for different LLM providers"""
    
    def __init__(self, provider: str, api_key: str):
        self.provider = provider.lower()
        self.api_key = api_key
        self._client = None
        
        # Initialize the appropriate client
        if self.provider == 'openai':
            self._client = openai.OpenAI(api_key=api_key)
        elif self.provider == 'anthropic':
            self._client = anthropic.Anthropic(api_key=api_key)
        elif self.provider == 'gemini':
            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel('gemini-pro')
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def test_connection(self) -> bool:
        """Test the connection to the LLM provider"""
        try:
            test_prompt = "Hello, this is a test. Please respond with 'OK'."
            
            if self.provider == 'openai':
                response = self._client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10
                )
                return bool(response.choices[0].message.content)
                
            elif self.provider == 'anthropic':
                response = self._client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": test_prompt}]
                )
                return bool(response.content[0].text)
                
            elif self.provider == 'gemini':
                response = self._client.generate_content(test_prompt)
                return bool(response.text)
                
        except Exception as e:
            logger.error(f"Connection test failed for {self.provider}: {e}")
            raise Exception(f"Failed to connect to {self.provider.upper()}: {str(e)}")
        
        return False
    
    async def generate_presentation_structure(self, text_content: str, guidance: str = "") -> Dict[str, Any]:
        """Generate presentation structure from text content"""
        try:
            prompt = self._create_structure_prompt(text_content, guidance)
            
            if self.provider == 'openai':
                response = self._client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are an expert presentation designer. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.7
                )
                content = response.choices[0].message.content
                
            elif self.provider == 'anthropic':
                response = self._client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=3000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
                
            elif self.provider == 'gemini':
                response = self._client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=3000,
                        temperature=0.7
                    )
                )
                content = response.text
            
            # Parse and validate the response
            presentation_data = self._parse_llm_response(content)
            
            # Generate speaker notes for each slide
            for slide in presentation_data.get('slides', []):
                slide['speaker_notes'] = await self._generate_speaker_notes(slide)
            
            return presentation_data
            
        except Exception as e:
            logger.error(f"Error generating presentation structure: {e}")
            # Return fallback structure
            return self._create_fallback_structure(text_content, guidance)
    
    def _create_structure_prompt(self, text_content: str, guidance: str = "") -> str:
        """Create the prompt for generating presentation structure"""
        
        base_prompt = f"""
Create a professional PowerPoint presentation from the following content. 
Analyze the text and create an appropriate number of slides (typically 5-12 slides).

CONTENT TO ANALYZE:
{text_content[:4000]}  

GUIDANCE: {guidance if guidance else "Create a professional, well-structured presentation"}

REQUIREMENTS:
1. Create a logical slide structure
2. Each slide should have a clear title and focused content
3. Use bullet points where appropriate
4. Determine appropriate slide types (title, content, bullets)
5. Make content engaging and professional

OUTPUT FORMAT (JSON ONLY):
{{
    "title": "Main Presentation Title",
    "subtitle": "Subtitle or brief description",
    "slides": [
        {{
            "title": "Slide Title",
            "type": "bullets|content|title",
            "content": ["Bullet point 1", "Bullet point 2"] OR "Paragraph content"
        }}
    ]
}}

Respond ONLY with valid JSON. No additional text or explanation.
"""
        return base_prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate structure
            if not isinstance(data, dict) or 'slides' not in data:
                raise ValueError("Invalid response structure")
            
            # Ensure required fields
            data.setdefault('title', 'AI Generated Presentation')
            data.setdefault('subtitle', 'Created with AI')
            
            if not isinstance(data['slides'], list) or len(data['slides']) == 0:
                raise ValueError("No slides generated")
            
            # Validate and fix slides
            validated_slides = []
            for i, slide in enumerate(data['slides']):
                if not isinstance(slide, dict):
                    continue
                
                validated_slide = {
                    'title': slide.get('title', f'Slide {i + 1}'),
                    'type': slide.get('type', 'content'),
                    'content': slide.get('content', f'Content for slide {i + 1}')
                }
                
                # Ensure content is in the right format
                if validated_slide['type'] == 'bullets':
                    if isinstance(validated_slide['content'], str):
                        # Convert string to bullet points
                        lines = [line.strip() for line in validated_slide['content'].split('\n') if line.strip()]
                        validated_slide['content'] = lines[:6]  # Limit to 6 bullets
                    elif isinstance(validated_slide['content'], list):
                        validated_slide['content'] = validated_slide['content'][:6]
                
                validated_slides.append(validated_slide)
            
            data['slides'] = validated_slides
            return data
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Response content: {response[:500]}...")
            raise Exception(f"Failed to parse AI response: {str(e)}")
    
    def _create_fallback_structure(self, text_content: str, guidance: str) -> Dict[str, Any]:
        """Create a fallback presentation structure if LLM fails"""
        logger.info("Creating fallback presentation structure")
        
        # Split content into chunks
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        chunks = []
        
        current_chunk = ""
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < 500:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Create slides from chunks
        slides = []
        for i, chunk in enumerate(chunks[:8]):  # Limit to 8 slides
            slide_title = f"Key Point {i + 1}"
            
            # Try to extract a title from the chunk
            lines = chunk.split('\n')
            if lines:
                first_line = lines[0].strip()
                if len(first_line) < 100:
                    slide_title = first_line
                    content = '\n'.join(lines[1:]).strip()
                else:
                    content = chunk
            else:
                content = chunk
            
            # Convert to bullet points if content has multiple lines
            if '\n' in content and len(content.split('\n')) > 1:
                bullets = [line.strip() for line in content.split('\n') if line.strip()]
                slides.append({
                    'title': slide_title,
                    'type': 'bullets',
                    'content': bullets[:5]  # Limit bullets
                })
            else:
                slides.append({
                    'title': slide_title,
                    'type': 'content',
                    'content': content[:800]  # Limit content length
                })
        
        return {
            'title': 'AI Generated Presentation',
            'subtitle': 'Based on your content',
            'slides': slides if slides else [{
                'title': 'Your Content',
                'type': 'content',
                'content': text_content[:800]
            }]
        }
    
    async def _generate_speaker_notes(self, slide: Dict[str, Any]) -> str:
        """Generate speaker notes for a slide"""
        try:
            if self.provider == 'openai':
                prompt = f"""
Create brief speaker notes (2-3 sentences) for this slide:
Title: {slide['title']}
Content: {slide['content']}

Keep notes professional and helpful for presentation delivery.
"""
                response = self._client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.5
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == 'anthropic':
                prompt = f"""
Create brief speaker notes (2-3 sentences) for this slide:
Title: {slide['title']}
Content: {slide['content']}

Keep notes professional and helpful for presentation delivery.
"""
                response = self._client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            
            elif self.provider == 'gemini':
                prompt = f"""
Create brief speaker notes (2-3 sentences) for this slide:
Title: {slide['title']}
Content: {slide['content']}

Keep notes professional and helpful for presentation delivery.
"""
                response = self._client.generate_content(prompt)
                return response.text.strip()
                
        except Exception as e:
            logger.warning(f"Could not generate speaker notes: {e}")
            return f"Present the key points about {slide['title']} clearly and engage with your audience."
        
        return ""
