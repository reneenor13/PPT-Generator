from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import tempfile
import os
from typing import Dict, List, Any
import re

class PPTXBuilder:
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.template_prs = Presentation(template_path)
        self.output_path = None
        
    def create_presentation(self, slide_structure: Dict[str, Any]) -> str:
        """Create a new presentation based on the slide structure"""
        
        # Create new presentation from template
        new_prs = Presentation(self.template_path)
        
        # Clear existing slides except the first one (we'll use it as template)
        slides_to_remove = list(new_prs.slides._sldIdLst)
        for slide_id in slides_to_remove[1:]:
            new_prs.slides._sldIdLst.remove(slide_id)
        
        # Get the template slide layout
        template_slide = new_prs.slides[0] if len(new_prs.slides) > 0 else None
        slide_layouts = new_prs.slide_layouts
        
        # Clear the template slide if it exists
        if template_slide:
            new_prs.slides._sldIdLst.remove(new_prs.slides._sldIdLst[0])
        
        # Create slides based on structure
        slides_data = slide_structure.get("slides", [])
        
        for i, slide_data in enumerate(slides_data):
            if i == 0:
                # Title slide
                slide = new_prs.slides.add_slide(slide_layouts[0])  # Title slide layout
                self._populate_title_slide(slide, slide_data, slide_structure.get("title", ""))
            else:
                # Content slide
                slide = new_prs.slides.add_slide(slide_layouts[1])  # Content slide layout
                self._populate_content_slide(slide, slide_data)
            
            # Add speaker notes if present
            if "speaker_notes" in slide_data:
                slide.notes_slide.notes_text_frame.text = slide_data["speaker_notes"]
        
        # Save the presentation
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as temp_file:
            self.output_path = temp_file.name
        
        new_prs.save(self.output_path)
        return self.output_path
    
    def _populate_title_slide(self, slide, slide_data: Dict, presentation_title: str):
        """Populate a title slide"""
        if slide.shapes.title:
            slide.shapes.title.text = presentation_title or slide_data.get("title", "")
        
        # Find subtitle placeholder
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == 1:  # Subtitle placeholder
                shape.text = slide_data.get("content", "")
                break
    
    def _populate_content_slide(self, slide, slide_data: Dict):
        """Populate a content slide"""
        if slide.shapes.title:
            slide.shapes.title.text = slide_data.get("title", "")
        
        # Find content placeholder
        content_placeholder = None
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == 1:  # Content placeholder
                content_placeholder = shape
                break
        
        if content_placeholder:
            content = slide_data.get("content", "")
            self._format_content_text(content_placeholder, content)
    
    def _format_content_text(self, placeholder, content: str):
        """Format text content with bullet points"""
        text_frame = placeholder.text_frame
        text_frame.clear()
        
        # Split content into bullet points
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if i == 0:
                p = text_frame.paragraphs[0]
            else:
                p = text_frame.add_paragraph()
            
            # Remove existing bullet markers
            clean_line = re.sub(r'^[-•*]\s*', '', line)
            p.text = clean_line
            p.level = 0
            
            # Set bullet point
            p.font.size = Pt(18)
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.output_path and os.path.exists(self.output_path):
            os.unlink(self.output_path)
