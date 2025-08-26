from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/file/stat/<path:filename>', methods=['GET'])
def stat_file(filename):
    try:
        file_stats = os.stat(filename)
        return jsonify({
            'size': file_stats.st_size,
            'modified_time': file_stats.st_mtime,
            'access_time': file_stats.st_atime
        }), 200
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/file/read/<path:filename>', methods=['GET'])
def read_file(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
        return jsonify({'content': content}), 200
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)