from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import traceback
import logging

# Import our custom modules
try:
    from pptx_builder import PowerPointBuilder
    from llm_client import LLMClient
    from utils import validate_file, parse_text_content
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are in the same directory")

app = Flask(__name__)
CORS(app, origins=['*'])  # Allow all origins for development

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET'])
def home():
    """Root endpoint to verify server is running"""
    return jsonify({
        "message": "Text to PowerPoint Generator API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate": "/generate-presentation"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "text-to-ppt-api"})

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for debugging"""
    return jsonify({
        "message": "Test endpoint working",
        "method": "GET",
        "timestamp": str(os.times())
    })

@app.route('/generate-presentation', methods=['POST', 'OPTIONS'])
def generate_presentation():
    """Main endpoint to generate PowerPoint presentations"""
    
    # Handle preflight CORS requests
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    
    try:
        logger.info("Received presentation generation request")
        
        # Log request details for debugging
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        logger.info(f"Request files: {list(request.files.keys())}")
        
        # Get form data
        text_content = request.form.get('text_content')
        guidance = request.form.get('guidance', '')
        api_provider = request.form.get('api_provider')
        api_key = request.form.get('api_key')
        template_file = request.files.get('template_file')
        
        logger.info(f"Text content length: {len(text_content) if text_content else 0}")
        logger.info(f"API provider: {api_provider}")
        logger.info(f"Template file: {template_file.filename if template_file else 'None'}")
        
        # Validation
        if not text_content:
            return jsonify({"error": "Text content is required"}), 400
        if not api_provider:
            return jsonify({"error": "API provider is required"}), 400
        if not api_key:
            return jsonify({"error": "API key is required"}), 400
        if not template_file:
            return jsonify({"error": "Template file is required"}), 400
        
        # Validate template file
        if not validate_file(template_file):
            return jsonify({"error": "Invalid template file. Please upload a .pptx or .potx file"}), 400
        
        logger.info("All validations passed, starting generation process")
        
        # Save template temporarily
        temp_template = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx')
        template_file.save(temp_template.name)
        template_path = temp_template.name
        temp_template.close()
        
        logger.info(f"Template saved to: {template_path}")
        
        # Initialize LLM client
        logger.info("Initializing LLM client")
        llm_client = LLMClient(api_provider, api_key)
        
        # Generate slide structure
        logger.info("Generating slide structure with AI")
        slide_structure = llm_client.generate_slide_structure(text_content, guidance)
        logger.info(f"Generated {len(slide_structure.get('slides', []))} slides")
        
        # Build PowerPoint
        logger.info("Building PowerPoint presentation")
        builder = PowerPointBuilder(template_path)
        output_path = builder.create_presentation(slide_structure)
        logger.info(f"Presentation built: {output_path}")
        
        # Clean up template file
        try:
            os.unlink(template_path)
        except:
            pass  # Don't fail if cleanup fails
        
        # Return the file
        return send_file(
            output_path,
            as_attachment=True,
            download_name='generated_presentation.pptx',
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
    
    except Exception as e:
        logger.error(f"Error generating presentation: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Clean up any temporary files
        try:
            if 'template_path' in locals():
                os.unlink(template_path)
        except:
            pass
        
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "details": "Check server logs for more information"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler"""
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint was not found",
        "available_endpoints": [
            "/",
            "/health", 
            "/test",
            "/generate-presentation"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "Something went wrong on the server"
    }), 500

### `backend/test_server.py` (Create this file for testing)
```python
#!/usr/bin/env python3
"""
Simple test script to verify backend functionality
"""
import requests
import sys
import os

def test_backend(base_url="http://localhost:5000"):
    """Test all backend endpoints"""
    print(f"Testing backend at: {base_url}")
    print("=" * 50)
    
    # Test 1: Root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
    
    print()
    
    # Test 2: Health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✓ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
    
    print()
    
    # Test 3: Test endpoint
    try:
        response = requests.get(f"{base_url}/test")
        print(f"✓ Test endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Test endpoint failed: {e}")
    
    print()
    
    # Test 4: Generate presentation (without files - should fail gracefully)
    try:
        response = requests.post(f"{base_url}/generate-presentation", data={})
        print(f"✓ Generate endpoint (empty): {response.status_code}")
        if response.status_code == 400:
            print(f"  Expected error: {response.json()}")
    except Exception as e:
        print(f"✗ Generate endpoint test failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    test_backend(base_url)
