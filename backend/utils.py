import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pptx', 'potx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    """Validate uploaded template file"""
    if not file:
        return False
    
    if not allowed_file(file.filename):
        return False
    
    # Check file size (basic check)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return False
    
    return True

def parse_text_content(text):
    """Basic text preprocessing"""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Basic markdown to text conversion
    text = text.replace('**', '').replace('*', '')
    text = text.replace('##', '').replace('#', '')
    
    return text

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    return secure_filename(filename)
