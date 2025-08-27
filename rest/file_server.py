from flask import Flask, request, jsonify, send_file
import os
import uuid as uuid_lib
from datetime import datetime
import mimetypes
from werkzeug.utils import secure_filename
import json
import logging


app = Flask(__name__)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/app/files")
METADATA_FILE = os.getenv("METADATA_FILE", "/app/metadata.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def handle_error(message, status_code=400):
    """Log error"""
    logger.error(message)
    response = jsonify({"error": message})
    response.status_code = status_code
    return response

# Metadata utilities
def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

metadata_store = load_metadata()


# Routes
@app.route('/file/<uuid>/stat/', methods=['GET'])
def stat_file(uuid):
    """Get file metadata"""
    try:
        uuid_lib.UUID(uuid)
    except ValueError:
        return handle_error("Invalid UUID format", 404)
    
    if uuid not in metadata_store:
        return handle_error("File not found", 404)
    
    file_info = metadata_store[uuid]
    
    return jsonify({
        'create_datetime': file_info['create_datetime'],
        'size': file_info['size'],
        'mimetype': file_info['mimetype'],
        'name': file_info['name']
    }), 200


@app.route('/file/<uuid>/read/', methods=['GET'])
def read_file(uuid):
    """Read file content"""
    try:
        uuid_lib.UUID(uuid)
    except ValueError:
        return handle_error("Invalid UUID format", 404)
    
    if uuid not in metadata_store:
        return handle_error("File not found", 404)
    
    file_info = metadata_store[uuid]
    file_path = file_info['file_path']
    
    if not os.path.exists(file_path):
        return handle_error("File missing on disk", 404)
    
    return send_file(
        file_path,
        mimetype=file_info['mimetype'],
        as_attachment=True,
        download_name=file_info['name']
    )


@app.route('/file/upload/', methods=['POST'])
def upload_file():
    """Upload a new file"""
    if 'file' not in request.files:
        return handle_error("No file provided", 400)
    
    file = request.files['file']
    if file.filename == '':
        return handle_error("No file selected", 400)
    
    file_uuid = str(uuid_lib.uuid4())
    filename = secure_filename(file.filename)
    
    mimetype = file.content_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    file_extension = os.path.splitext(filename)[1]
    stored_filename = f"{file_uuid}{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, stored_filename)
    
    try:
        file.save(file_path)
    except Exception as e:
        return handle_error(f"Failed to save file: {e}", 500)
    
    file_size = os.path.getsize(file_path)
    metadata_store[file_uuid] = {
        "name": filename,
        "size": file_size,
        "mimetype": mimetype,
        "create_datetime": datetime.utcnow().isoformat() + "Z",
        "file_path": file_path
    }
    save_metadata(metadata_store)
    
    return jsonify({
        'uuid': file_uuid,
        'message': 'File uploaded successfully'
    }), 201


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat() + "Z"}), 200


# =====================
# Global error handler
# =====================
@app.errorhandler(Exception)
def global_error_handler(e):
    logger.exception("Unhandled exception occurred")
    return handle_error(str(e), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
