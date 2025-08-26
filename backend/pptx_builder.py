from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import os
import tempfile
import shutil

class PowerPointBuilder:
    def __init__(self, template_path):
        self.template_path = template_path
        self.template_prs = Presentation(template_path)
        self.output_prs = None
        self.extracted_styles = self._extract_template_styles()
    
    def _extract_template_styles(self):
        """Extract colors, fonts, and layouts from template"""
        styles = {
            'layouts': [],
            'colors': [],
            'fonts': [],
            'images': []
        }
        
        # Extract slide layouts
        for layout in self.template_prs.slide_layouts:
            styles['layouts'].append(layout)
        
        # Extract colors and fonts from existing slides
        for slide in self.template_prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame'):
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if run.font.color.rgb:
                                styles['colors'].append(run.font.color.rgb)
                            if run.font.name:
                                styles['fonts'].append(run.font.name)
                
                # Extract images
                if shape.shape_type == 13:  # Picture
                    styles['images'].append(shape)
        
        return styles
    
    def create_presentation(self, slide_structure):
        """Create new presentation based on template and slide structure"""
        # Create new presentation from template
        self.output_prs = Presentation(self.template_path)
        
        # Clear existing slides except layouts
        slide_count = len(self.output_prs.slides)
        for i in range(slide_count - 1, -1, -1):
            rId = self.output_prs.slides._sldIdLst[i].rId
            self.output_prs.part.drop_rel(rId)
            del self.output_prs.slides._sldIdLst[i]
        
        # Add title slide
        self._add_title_slide(slide_structure['title'])
        
        # Add content slides
        for slide_data in slide_structure['slides']:
            self._add_content_slide(slide_data)
        
        # Save presentation
        output_path = tempfile.mktemp(suffix='.pptx')
        self.output_prs.save(output_path)
        
        return output_path
    
    def _add_title_slide(self, title):
        """Add title slide using template layout"""
        title_layout = self.output_prs.slide_layouts[0]  # Usually title slide
        slide = self.output_prs.slides.add_slide(title_layout)
        
        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = title
        
        # Apply template styling
        self._apply_template_styling(slide)
    
    def _add_content_slide(self, slide_data):
        """Add content slide with bullet points"""
        content_layout = self.output_prs.slide_layouts[1]  # Usually content layout
        slide = self.output_prs.slides.add_slide(content_layout)
        
        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = slide_data['title']
        
        # Add content
        if len(slide.shapes.placeholders) > 1:
            content_placeholder = slide.shapes.placeholders[1]
            text_frame = content_placeholder.text_frame
            text_frame.clear()
            
            for i, bullet_point in enumerate(slide_data['content']):
                p = text_frame.paragraphs[0] if i == 0 else text_frame.add_paragraph()
                p.text = bullet_point
                p.level = 0
        
        # Apply template styling
        self._apply_template_styling(slide)
    
    def _apply_template_styling(self, slide):
        """Apply extracted template styles to slide"""
        for shape in slide.shapes:
            if hasattr(shape, 'text_frame'):
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        # Apply fonts and colors from template
                        if self.extracted_styles['fonts']:
                            run.font.name = self.extracted_styles['fonts'][0]
                        if self.extracted_styles['colors']:
                            run.font.color.rgb = self.extracted_styles['colors'][0]
