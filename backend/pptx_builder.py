
from pptx import Presentation

def build_presentation(template_file, outline, output_path):
    prs = Presentation(template_file)
    layout = prs.slide_layouts[1]  # title+content

    for slide_data in outline:
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = slide_data["title"]
        body = slide.placeholders[1]
        body.text = "\n".join(slide_data["bullets"])

    prs.save(output_path)
