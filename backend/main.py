from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
from pptx_builder import build_presentation
from llm_client import get_slide_outline
import tempfile

app = FastAPI()

@app.post("/generate-ppt")
async def generate_ppt(
    text: str = Form(...),
    guidance: str = Form(""),
    api_key: str = Form(...),
    file: UploadFile = None
):
    outline = get_slide_outline(text, guidance, api_key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
        build_presentation(file.file, outline, tmp.name)
        return FileResponse(tmp.name, filename="generated.pptx")

