from flask import Flask, request, jsonify, send_file
import os
import uuid as uuid_lib
from datetime import datetime
import mimetypes
from werkzeug.utils import secure_filename
import json
import logging


app = Flask(__name__)

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "files"))
METADATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "files", "metadata.json"))

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
    logger.info(f"Loading metadata from: {METADATA_FILE}")
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} files from metadata")
            for uuid, info in data.items():
                logger.info(f"  - {uuid}: {info['name']} ({info['size']} bytes)")
            return data
    logger.warning(f"Metadata file not found: {METADATA_FILE}")
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to: {METADATA_FILE}")

metadata_store = load_metadata()


# Routes
@app.route('/file/<uuid>/stat/', methods=['GET'])
def stat_file(uuid):
    """Get file metadata"""
    logger.info(f"Stat request for UUID: {uuid}")
    try:
        uuid_lib.UUID(uuid)
    except ValueError:
        return handle_error("Invalid UUID format", 400)
    
    if uuid not in metadata_store:
        logger.error(f"UUID not found in metadata: {uuid}")
        logger.info(f"Available UUIDs: {list(metadata_store.keys())}")
        return handle_error("File not found", 404)
    
    file_info = metadata_store[uuid]
    logger.info(f"Found file: {file_info['name']} ({file_info['size']} bytes)")
    
    return jsonify({
        'create_datetime': file_info['create_datetime'],
        'size': file_info['size'],
        'mimetype': file_info['mimetype'],
        'name': file_info['name']
    }), 200


@app.route('/file/<uuid>/read/', methods=['GET'])
def read_file(uuid):
    """Read file content"""
    logger.info(f"Read request for UUID: {uuid}")
    try:
        uuid_lib.UUID(uuid)
    except ValueError:
        return handle_error("Invalid UUID format", 400)
    
    if uuid not in metadata_store:
        return handle_error("File not found", 404)
    
    file_info = metadata_store[uuid]
    file_path = file_info['file_path']
    
    # Convert relative path to absolute path if needed
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", file_path))
    
    logger.info(f"Reading file from: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File missing on disk: {file_path}")
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
    
    logger.info(f"File uploaded by michalomegalul: {filename} -> {file_uuid} ({file_size} bytes)")
    
    return jsonify({
        'uuid': file_uuid,
        'message': 'File uploaded successfully',
        'author': 'michalomegalul',
        'timestamp': datetime.utcnow().isoformat() + "Z"
    }), 201


@app.route('/files/', methods=['GET'])
def list_files():
    """List all available files for testing"""
    return jsonify({
        'files': [
            {
                'uuid': uuid, 
                'name': info['name'], 
                'size': info['size'],
                'mimetype': info['mimetype'],
                'created': info['create_datetime']
            }
            for uuid, info in metadata_store.items()
        ],
        'total_files': len(metadata_store),
        'storage_location': UPLOAD_FOLDER,
        'metadata_file': METADATA_FILE,
        'author': 'michalomegalul'
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.utcnow().isoformat() + "Z",
        'upload_folder': UPLOAD_FOLDER,
        'metadata_file': METADATA_FILE,
        'files_count': len(metadata_store),
        'available_uuids': list(metadata_store.keys()),
        'author': 'michalomegalul',
        'current_time': '2025-08-27 14:34:31'
    }), 200


@app.errorhandler(Exception)
def global_error_handler(e):
    logger.exception("Unhandled exception occurred")
    return handle_error(str(e), 500)


if __name__ == '__main__':
    logger.info(f"Starting File Server by michalomegalul on 2025-08-27 14:34:31")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Metadata file: {METADATA_FILE}")
    logger.info(f"Available files: {len(metadata_store)}")
    if metadata_store:
        logger.info("Available UUIDs:")
        for uuid, info in metadata_store.items():
            logger.info(f"  - {uuid}: {info['name']}")
    app.run(host='0.0.0.0', port=5000, debug=True)