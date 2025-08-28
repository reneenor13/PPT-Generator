import os
import re
import zipfile
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# backend/utils.py

def validate_pptx_file(file_path: str) -> bool:
    """
    Validates if the given file is a .pptx file.
    Returns True if valid, False otherwise.
    """
    return file_path.endswith(".pptx")

def validate_pptx_file(file_path: str) -> bool:
    """
    Validate if a file is a valid PowerPoint file (.pptx or .potx).
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return False

        if not file_path.lower().endswith(('.pptx', '.potx')):
            logger.error(f"Invalid file extension: {file_path}")
            return False

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                required_files = [
                    '[Content_Types].xml',
                    '_rels/.rels'
                ]
                zip_contents = zip_file.namelist()

                for required_file in required_files:
                    if required_file not in zip_contents:
                        logger.error(f"Missing required file: {required_file}")
                        return False

                has_slides = any(name.startswith('ppt/slides/') for name in zip_contents)
                has_layouts = any(name.startswith('ppt/slideLayouts/') for name in zip_contents)

                if not (has_slides or has_layouts):
                    if not any(name.startswith('ppt/') for name in zip_contents):
                        logger.error("No PowerPoint structure found")
                        return False

                logger.info(f"✅ Valid PowerPoint file: {os.path.basename(file_path)}")
                return True

        except zipfile.BadZipFile:
            logger.error(f"Not a valid ZIP archive: {file_path}")
            return False

    except Exception as e:
        logger.error(f"Error validating PowerPoint file {file_path}: {e}")
        return False


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize a filename to be safe for file systems.
    """
    try:
        if not filename:
            return "presentation"

        invalid_chars = r'[<>:"|?*\\/]'
        sanitized = re.sub(invalid_chars, '_', filename)
        sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
        sanitized = re.sub(r'[_\s]+', '_', sanitized)
        sanitized = sanitized.strip(' ._')

        if not sanitized:
            sanitized = "presentation"

        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_.')
        sanitized = sanitized.rstrip(' .')

        reserved = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        if sanitized.upper() in reserved:
            sanitized = f"_{sanitized}"

        return sanitized

    except Exception as e:
        logger.warning(f"Error sanitizing filename '{filename}': {e}")
        return "presentation"


def split_text_into_sections(text: str, max_length: int = 800) -> List[str]:
    """
    Split input text into smaller sections for slides.
    """
    try:
        if not text:
            return []

        text = text.replace("\r\n", "\n").strip()
        paragraphs = re.split(r"\n\s*\n", text)

        chunks, current = [], ""
        for para in paragraphs:
            if len(current) + len(para) <= max_length:
                current += ("\n\n" if current else "") + para
            else:
                if current:
                    chunks.append(current.strip())
                if len(para) <= max_length:
                    current = para
                else:
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
    Map text chunks into slide-friendly structures.
    """
    slides = []
    for i, chunk in enumerate(chunks, start=1):
        title = f"Slide {i}"
        if guidance:
            title = f"{guidance} – {i}"
        slides.append({"title": title, "content": chunk})
    return slides


def sanitize_api_key(api_key: str) -> str:
    """
    Ensure API key format looks valid without storing it.
    """
    if not api_key:
        return ""
    api_key = api_key.strip()
    if not re.match(r"^[A-Za-z0-9_\-\.\|:]+$", api_key):
        logger.warning("API key contains invalid characters")
    return api_key
