import os
import sys
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import backend modules
try:
    from backend.llm_client import LLMClient
    from backend.pptx_builder import create_presentation_from_template
    from backend.utils import validate_pptx_file, sanitize_filename
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure backend modules are in the backend/ directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Presentation Generator",
    description="Transform text into professional PowerPoint presentations",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "50000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Global variables
temp_files = []

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 AI Presentation Generator Starting Up")
    logger.info(f"📊 Max file size: {MAX_FILE_SIZE_MB}MB")
    logger.info(f"📝 Max text length: {MAX_TEXT_LENGTH} characters")
    logger.info(f"🔧 Debug mode: {DEBUG}")
    logger.info("✅ Application ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event - cleanup temp files"""
    logger.info("🧹 Cleaning up temporary files...")
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.info(f"🗑️ Removed: {temp_file}")
        except Exception as e:
            logger.warning(f"⚠️ Could not remove {temp_file}: {e}")
    logger.info("👋 AI Presentation Generator Shutting Down")

def cleanup_temp_file(filepath: str):
    """Add temp file to cleanup list and remove immediately if possible"""
    if filepath:
        temp_files.append(filepath)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"🗑️ Cleaned up: {os.path.basename(filepath)}")
        except Exception as e:
            logger.warning(f"⚠️ Could not clean up {filepath}: {e}")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Invalid request data",
            "details": exc.errors(),
            "status_code": 422
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "status_code": 500
        }
    )

# Static file serving
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main HTML page"""
    try:
        frontend_path = Path("frontend/index.html")
        if not frontend_path.exists():
            raise HTTPException(status_code=404, detail="Frontend not found")
        
        with open(frontend_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return HTMLResponse(content=content)
    
    except Exception as e:
        logger.error(f"Error serving frontend: {e}")
        return HTMLResponse(
            content="<h1>AI Presentation Generator</h1><p>Frontend loading error. Please check server logs.</p>",
            status_code=500
        )

@app.get("/App.js")
async def serve_app_js():
    """Serve the JavaScript file"""
    try:
        js_path = Path("frontend/App.js")
        if not js_path.exists():
            raise HTTPException(status_code=404, detail="App.js not found")
        
        return FileResponse(
            js_path,
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache"}
        )
    
    except Exception as e:
        logger.error(f"Error serving App.js: {e}")
        raise HTTPException(status_code=500, detail="Could not load JavaScript")

@app.get("/favicon.ico")
async def serve_favicon():
    """Serve favicon"""
    favicon_path = Path("public/logo.png")
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/png")
    else:
        # Return empty response if no favicon
        return JSONResponse(content={}, status_code=204)

# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Presentation Generator",
        "version": "1.0.0",
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "max_text_length": MAX_TEXT_LENGTH
    }

@app.get("/api/info")
async def app_info():
    """Get application information"""
    return {
        "name": "AI Presentation Generator",
        "version": "1.0.0",
        "description": "Transform text into professional PowerPoint presentations",
        "supported_formats": [".pptx", ".potx"],
        "supported_llms": ["openai", "anthropic", "gemini"],
        "limits": {
            "max_file_size_mb": MAX_FILE_SIZE_MB,
            "max_text_length": MAX_TEXT_LENGTH
        }
    }

@app.post("/api/generate")
async def generate_presentation(
    text_content: str = Form(..., min_length=10, max_length=MAX_TEXT_LENGTH),
    guidance: Optional[str] = Form("", max_length=500),
    llm_provider: str = Form(..., regex="^(openai|anthropic|gemini)$"),
    api_key: str = Form(..., min_length=10),
    template_file: UploadFile = File(...)
):
    """Generate PowerPoint presentation from text"""
    
    temp_template_path = None
    temp_output_path = None
    
    try:
        logger.info("🎯 Starting presentation generation")
        
        # Validate inputs
        if len(text_content.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text content is too short (minimum 10 characters)")
        
        if not api_key or len(api_key.strip()) < 10:
            raise HTTPException(status_code=400, detail="Valid API key is required")
        
        # Validate file
        logger.info("📁 Validating template file")
        if not template_file.filename:
            raise HTTPException(status_code=400, detail="No template file provided")
        
        if not template_file.filename.lower().endswith(('.pptx', '.potx')):
            raise HTTPException(status_code=400, detail="Template must be a .pptx or .potx file")
        
        # Check file size
        file_size = 0
        content = await template_file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Template file is empty")
        
        # Save template to temporary file
        logger.info("💾 Saving template file")
        temp_template_path = tempfile.mktemp(suffix='.pptx')
        with open(temp_template_path, 'wb') as f:
            f.write(content)
        
        # Validate PowerPoint file
        if not validate_pptx_file(temp_template_path):
            raise HTTPException(status_code=400, detail="Invalid PowerPoint file format")
        
        # Initialize LLM client
        logger.info(f"🤖 Initializing {llm_provider.upper()} client")
        llm_client = LLMClient(provider=llm_provider, api_key=api_key.strip())
        
        # Test LLM connection
        try:
            await llm_client.test_connection()
        except Exception as e:
            logger.error(f"LLM connection failed: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to connect to {llm_provider.upper()}. Please check your API key."
            )
        
        # Generate presentation structure
        logger.info("🧠 Analyzing content and generating structure")
        try:
            presentation_data = await llm_client.generate_presentation_structure(
                text_content.strip(), 
                guidance.strip() if guidance else ""
            )
            
            if not presentation_data or not presentation_data.get('slides'):
                raise Exception("No slides generated from content")
                
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze content: {str(e)}"
            )
        
        # Create presentation
        logger.info("🎨 Creating PowerPoint presentation")
        temp_output_path = tempfile.mktemp(suffix='.pptx')
        
        try:
            success = await create_presentation_from_template(
                template_path=temp_template_path,
                output_path=temp_output_path,
                presentation_data=presentation_data,
                llm_client=llm_client
            )
            
            if not success:
                raise Exception("Presentation creation failed")
                
        except Exception as e:
            logger.error(f"Presentation creation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create presentation: {str(e)}"
            )
        
        # Verify output file
        if not os.path.exists(temp_output_path) or os.path.getsize(temp_output_path) == 0:
            raise HTTPException(status_code=500, detail="Generated presentation file is invalid")
        
        # Generate safe filename
        base_name = sanitize_filename(presentation_data.get('title', 'AI_Generated_Presentation'))
        safe_filename = f"{base_name}.pptx"
        
        logger.info(f"✅ Presentation generated successfully: {safe_filename}")
        
        # Return the file
        def cleanup_after_response():
            """Cleanup function to run after response is sent"""
            cleanup_temp_file(temp_template_path)
            cleanup_temp_file(temp_output_path)
        
        # Schedule cleanup (run after a delay to ensure file is downloaded)
        asyncio.create_task(asyncio.sleep(10))  # Wait 10 seconds then cleanup
        
        return FileResponse(
            path=temp_output_path,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            filename=safe_filename,
            headers={
                "Content-Disposition": f"attachment; filename=\"{safe_filename}\"",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        cleanup_temp_file(temp_template_path)
        cleanup_temp_file(temp_output_path)
        raise
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in generate_presentation: {e}", exc_info=True)
        cleanup_temp_file(temp_template_path)
        cleanup_temp_file(temp_output_path)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# 404 handler for unknown routes
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Catch-all route for unknown paths"""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail=f"API endpoint not found: /{full_path}")
    else:
        # For non-API routes, serve the main page (SPA behavior)
        return await serve_frontend()

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🌟 Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info" if DEBUG else "warning",
        reload=DEBUG
    )
