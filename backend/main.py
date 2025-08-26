from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from llm_client import LLMClient
from pptx_builder import create_presentation
import tempfile
import os

app = FastAPI(title="Text to PowerPoint Generator")

# Enable CORS for frontend hosted separately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"status": "running", "message": "Text to PowerPoint Generator API"}

@app.post("/generate-presentation")
async def generate_presentation(
    text: str = Form(...),
    guidance: str = Form(""),
    llm_provider: str = Form(...),
    api_key: str = Form(...),
    template: UploadFile = File(...)
):
    try:
        # Read template into temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_template:
            tmp_template.write(await template.read())
            template_path = tmp_template.name

        # Generate slide content using LLM
        llm = LLMClient(provider=llm_provider, api_key=api_key)
        slides = llm.generate_slide_outline(text, guidance)

        # Build presentation using template
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx").name
        create_presentation(slides, template_path, output_path)

        # Clean up template
        os.remove(template_path)

        return FileResponse(
            path=output_path,
            filename="generated_presentation.pptx",
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
