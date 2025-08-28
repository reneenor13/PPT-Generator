import os
import re
from typing import Optional

def validate_file_type(filename: str) -> bool:
    """Validate that the uploaded file is a PowerPoint file"""
    if not filename:
        return False
    
    allowed_extensions = ['.pptx', '.potx']
    file_extension = os.path.splitext(filename.lower())[1]
    return file_extension in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent security issues"""
    # Remove path separators and special characters
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    return filename

def validate_api_key(provider: str, api_key: str) -> bool:
    """Basic validation of API key format"""
    if not api_key or len(api_key) < 10:
        return False
    
    if provider.lower() == "openai" and not api_key.startswith("sk-"):
        return False
    elif provider.lower() == "anthropic" and not api_key.startswith("sk-ant-"):
        return False
    
    return True

def estimate_slide_count(text_length: int, guidance: str = "") -> int:
    """Estimate optimal number of slides based on text length"""
    words = text_length // 5  # Rough word count estimation
    
    if "pitch" in guidance.lower() or "investor" in guidance.lower():
        # Pitch decks are typically shorter
        return min(max(6, words // 100), 10)
    elif "technical" in guidance.lower():
        # Technical presentations might need more slides
        return min(max(8, words // 80), 15)
    else:
        # General presentation
        return min(max(5, words // 120), 12)
