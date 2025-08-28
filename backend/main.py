from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import tempfile
import os
import json
from typing import Optional
import asyncio

from backend.llm_client import LLMClient
from backend.pptx_builder import PPTXBuilder
from backend.utils import validate_file_type, sanitize_filename

# Create FastAPI app
app = FastAPI(title="AI Presentation Generator", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend assets)
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve the main HTML page
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main HTML file"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend not found</h1><p>Please make sure frontend/index.html exists</p>", 
            status_code=404
        )

# Serve individual static files
@app.get("/App.js")
async def serve_app_js():
    """Serve the main JavaScript file"""
    try:
        return FileResponse("frontend/App.js", media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="App.js not found")

@app.get("/favicon.ico")
async def serve_favicon():
    """Serve favicon"""
    try:
        return FileResponse("public/logo.png", media_type="image/png")
    except FileNotFoundError:
        # Return empty response if no favicon
        return HTMLResponse(content="", status_code=204)

# API Routes
@app.post("/api/generate")
async def generate_presentation(
    text: str = Form(...),
    guidance: str = Form(""),
    llm_provider: str = Form(...),
    api_key: str = Form(...),
    template_file: UploadFile = File(...)
):
    """Generate a PowerPoint presentation from text and template"""
    
    try:
        # Validate inputs
        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Text content is too short. Please provide at least 10 characters."
            )
        
        if len(text) > 100000:  # 100k character limit
            raise HTTPException(
                status_code=400, 
                detail="Text content is too long. Please limit to 100,000 characters."
            )
        
        if not llm_provider:
            raise HTTPException(status_code=400, detail="Please select an LLM provider.")
        
        if not api_key or len(api_key.strip()) < 10:
            raise HTTPException(status_code=400, detail="Please provide a valid API key.")
        
        if not template_file or not template_file.filename:
            raise HTTPException(status_code=400, detail="Please upload a PowerPoint template file.")
        
        # Validate file type
        if not validate_file_type(template_file.filename):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload .pptx or .potx files only."
            )
        
        # Validate file size (10MB limit)
        if template_file.size and template_file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail="File size too large. Please upload files smaller than 10MB."
            )
        
        # Save uploaded template to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as temp_template:
            content = await template_file.read()
            temp_template.write(content)
            temp_template_path = temp_template.name
        
        try:
            # Initialize LLM client
            llm_client = LLMClient(llm_provider, api_key)
            
            # Generate slide structure using LLM
            slide_structure = await llm_client.generate_slide_structure(text, guidance)
            
            # Validate slide structure
            if not slide_structure or "slides" not in slide_structure:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to generate slide structure. Please try again."
                )
            
            if len(slide_structure["slides"]) == 0:
                raise HTTPException(
                    status_code=500, 
                    detail="No slides generated. Please provide more content."
                )
            
            # Build presentation
            builder = PPTXBuilder(temp_template_path)
            output_path = builder.create_presentation(slide_structure)
            
            if not os.path.exists(output_path):
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to create presentation file."
                )
            
            # Return the generated presentation
            return FileResponse(
                output_path,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                filename="generated_presentation.pptx",
                headers={
                    "Content-Disposition": "attachment; filename=generated_presentation.pptx"
                }
            )
        
        finally:
            # Clean up template file
            if os.path.exists(temp_template_path):
                try:
                    os.unlink(temp_template_path)
                except:
                    pass  # Ignore cleanup errors
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the actual error for debugging
        print(f"Unexpected error in generate_presentation: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Return generic error message to user
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "AI Presentation Generator is running",
        "version": "1.0.0"
    }

@app.get("/api/info")
async def app_info():
    """Get application information"""
    return {
        "name": "AI Presentation Generator",
        "version": "1.0.0",
        "description": "Transform text into professional PowerPoint presentations using AI",
        "supported_providers": ["openai", "anthropic", "gemini"],
        "max_file_size": "10MB",
        "max_text_length": "100,000 characters"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return HTMLResponse(
        content="""
        <html>
            <head><title>Page Not Found</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
                <h1>404 - Page Not Found</h1>
                <p>The requested page could not be found.</p>
                <a href="/" style="color: #3b82f6; text-decoration: none;">← Go back to home</a>
            </body>
        </html>
        """,
        status_code=404
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle 500 errors"""
    return HTMLResponse(
        content="""
        <html>
            <head><title>Server Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong on our end. Please try again later.</p>
                <a href="/" style="color: #3b82f6; text-decoration: none;">← Go back to home</a>
            </body>
        </html>
        """,
        status_code=500
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 AI Presentation Generator started successfully!")
    print(f"📁 Frontend directory exists: {os.path.exists('frontend')}")
    print(f"📁 Backend directory exists: {os.path.exists('backend')}")
    
    # Check for required files
    required_files = [
        "backend/llm_client.py",
        "backend/pptx_builder.py", 
        "backend/utils.py",
        "frontend/index.html",
        "frontend/App.js"
    ]
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        print(f"📄 {file_path}: {'✅' if exists else '❌'}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 AI Presentation Generator shutting down...")

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Render sets this automatically)
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🌟 Starting AI Presentation Generator on port {port}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
