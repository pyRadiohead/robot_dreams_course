"""Presentation Layer - Flask API Endpoint"""
from typing import Tuple, Dict, Any
from flask import Flask, request, jsonify, Response
from bll.conversion_service import ConversionService

app = Flask(__name__)


@app.route('/', methods=['POST'])
def main() -> Tuple[Response, int]:
    """
    Endpoint to convert JSON files to AVRO format

    Request JSON:
        {
            "raw_dir": "/path/to/json/files",
            "stg_dir": "/path/to/avro/output"
        }

    Returns:
        JSON response with status
    """
    # 1. Validate request
    data: Dict[str, Any] = request.json

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    raw_dir: str = data.get('raw_dir')
    stg_dir: str = data.get('stg_dir')

    if not raw_dir or not stg_dir:
        return jsonify({"error": "Missing required fields: raw_dir, stg_dir"}), 400

    # 2. Execute business logic
    try:
        service = ConversionService()
        result = service.convert_directory(raw_dir, stg_dir)

        return jsonify(result), 201

    except Exception as e:
        return jsonify({
            "error": "Conversion failed",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(port=8082)