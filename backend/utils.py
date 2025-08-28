import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def split_text_into_sections(text: str, max_length: int = 800) -> List[str]:
    """
    Split input text into smaller sections suitable for slides.
    Attempts to split on paragraph breaks, then sentences if needed.
    
    Args:
        text (str): The input text (markdown or prose)
        max_length (int): Maximum characters per section
    
    Returns:
        List[str]: List of text chunks
    """
    try:
        if not text:
            return []

        # Normalize newlines
        text = text.replace("\r\n", "\n").strip()

        # First split by double newlines (paragraphs)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) <= max_length:
                current += ("\n\n" if current else "") + para
            else:
                if current:
                    chunks.append(current.strip())
                if len(para) <= max_length:
                    current = para
                else:
                    # Split long paragraph into sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    temp = ""
                    for sent in sentences:
                        if len(temp) + len(sent) <= max_length:
                            temp += " " + sent
                        else:
                            if temp:
                                chunks.append(temp.strip())
                            temp = sent
                    if temp:
                        current = temp
                    else:
                        current = ""
        if current:
            chunks.append(current.strip())

        return chunks

    except Exception as e:
        logger.error(f"Error splitting text: {e}")
        return [text]


def map_text_to_slides(chunks: List[str], guidance: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Map text chunks into a slide-friendly structure.
    Optionally use guidance (tone, purpose) to adjust titles.
    
    Args:
        chunks (List[str]): List of text sections
        guidance (Optional[str]): Extra user instruction
    
    Returns:
        List[Dict[str, str]]: Each dict contains 'title' and 'content'
    """
    slides = []
    for i, chunk in enumerate(chunks, start=1):
        title = f"Slide {i}"
        if guidance:
            title = f"{guidance} – {i}"
        slides.append({
            "title": title,
            "content": chunk
        })
    return slides


def sanitize_api_key(api_key: str) -> str:
    """
    Basic check to ensure API key format looks valid without storing it.
    
    Args:
        api_key (str): The provided API key
    
    Returns:
        str: Sanitized/trimmed API key
    """
    if not api_key:
        return ""
    api_key = api_key.strip()
    if not re.match(r"^[A-Za-z0-9_\-\.\|:]+$", api_key):
        logger.warning("API key contains invalid characters")
    return api_key
