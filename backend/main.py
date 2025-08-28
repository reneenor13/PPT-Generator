from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile
import os
import json
from typing import Optional
from pydantic import BaseModel

from llm_client import LLMClient
from pptx_builder import PPTXBuilder
from utils import validate_file_type, sanitize_filename

app = FastAPI(title="Presentation Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    text: str
    guidance: Optional[str] = ""
    llm_provider: str
    api_key: str

@app.post("/generate")
async def generate_presentation(
    text: str = Form(...),
    guidance: str = Form(""),
    llm_provider: str = Form(...),
    api_key: str = Form(...),
    template_file: UploadFile = File(...)
):
    try:
        # Validate template file
        if not validate_file_type(template_file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload .pptx or .potx files only.")
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as temp_template:
            temp_template.write(await template_file.read())
            temp_template_path = temp_template.name
        
        # Initialize LLM client
        llm_client = LLMClient(llm_provider, api_key)
        
        # Generate slide structure using LLM
        slide_structure = await llm_client.generate_slide_structure(text, guidance)
        
        # Build presentation
        builder = PPTXBuilder(temp_template_path)
        output_path = builder.create_presentation(slide_structure)
        
        # Clean up template file
        os.unlink(temp_template_path)
        
        # Return the generated presentation
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename="generated_presentation.pptx",
            headers={"Content-Disposition": "attachment; filename=generated_presentation.pptx"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
