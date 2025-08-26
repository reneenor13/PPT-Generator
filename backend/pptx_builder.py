from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

def create_presentation(slide_texts, template_file, output_file):
    template = Presentation(template_file)
    prs = Presentation(template_file)

    for slide_text in slide_texts:
        # Use first layout as default
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        if "\n" in slide_text:
            title, content = slide_text.split("\n", 1)
        else:
            title, content = slide_text, ""
        if slide.shapes.title:
            slide.shapes.title.text = title
        else:
            # Add textbox if title not present
            textbox = slide.shapes.add_textbox(left=Pt(50), top=Pt(50), width=Pt(600), height=Pt(100))
            textbox.text = title

        # Add content to first placeholder or create new textbox
        if slide.placeholders:
            for ph in slide.placeholders:
                if ph.placeholder_format.type == 1:  # BODY type
                    ph.text = content
                    break
        else:
            textbox = slide.shapes.add_textbox(left=Pt(50), top=Pt(150), width=Pt(600), height=Pt(400))
            textbox.text = content

    prs.save(output_file)
