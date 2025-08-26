import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from llm_client import LLMClient
from pptx_builder import build_pptx
import tempfile

# Create FastAPI app
app = FastAPI(title="Text to PowerPoint Generator API")

# Enable CORS for all origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "running", "message": "Text to PowerPoint Generator API"}

# Generate PowerPoint endpoint
@app.post("/generate-presentation")
async def generate_presentation(
    text: str = Form(...),
    guidance: str = Form(""),
    llm_provider: str = Form(...),
    api_key: str = Form(...),
    template_file: UploadFile = File(...)
):
    # Validate LLM provider
    if llm_provider.lower() not in ["openai", "anthropic", "google", "gemini"]:
        raise HTTPException(status_code=400, detail="Unsupported LLM provider")

    # Save uploaded template temporarily
    try:
        temp_template = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
        template_path = temp_template.name
        content = await template_file.read()
        temp_template.write(content)
        temp_template.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save template: {e}")

    # Generate slides outline
    try:
        llm = LLMClient(provider=llm_provider.lower(), api_key=api_key)
        slides = llm.generate_slide_outline(text, guidance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")

    # Build PowerPoint file
    try:
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
        build_pptx(slides, template_path, output_file.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build PPTX: {e}")

    return FileResponse(output_file.name, filename="generated_presentation.pptx")
