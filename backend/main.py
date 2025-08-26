from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from pptx_builder import PowerPointBuilder
from llm_client import LLMClient
from utils import validate_file, parse_text_content
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/generate-presentation', methods=['POST'])
def generate_presentation():
    try:
        # Get form data
        text_content = request.form.get('text_content')
        guidance = request.form.get('guidance', '')
        api_provider = request.form.get('api_provider')
        api_key = request.form.get('api_key')
        template_file = request.files.get('template_file')
        
        # Validation
        if not all([text_content, api_provider, api_key, template_file]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Validate template file
        if not validate_file(template_file):
            return jsonify({"error": "Invalid template file"}), 400
        
        # Save template temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as temp_template:
            template_file.save(temp_template.name)
            template_path = temp_template.name
        
        # Initialize LLM client
        llm_client = LLMClient(api_provider, api_key)
        
        # Generate slide structure
        slide_structure = llm_client.generate_slide_structure(text_content, guidance)
        
        # Build PowerPoint
        builder = PowerPointBuilder(template_path)
        output_path = builder.create_presentation(slide_structure)
        
        # Clean up template file
        os.unlink(template_path)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name='generated_presentation.pptx',
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
    
    except Exception as e:
        logger.error(f"Error generating presentation: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
