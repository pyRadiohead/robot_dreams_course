"""Presentation Layer - Flask API Endpoint"""
import os
from typing import Tuple, Dict, Any, Optional
from flask import Flask, request, jsonify, Response
from bll.sales_service import SalesService

app = Flask(__name__)

# Configuration
API_BASE_URL = "https://fake-api-vycpfa6oca-uc.a.run.app"


@app.route('/', methods=['POST'])
def main() -> Tuple[Response, int]:
    """
    Endpoint to fetch and store sales data

    Request JSON:
        {
            "date": "2022-08-09",
            "raw_dir": "/path/to/output"
        }

    Returns:
        JSON response with status
    """
    # 1. Validate request
    data: Dict[str, Any] = request.json

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    date: str = data.get('date')
    output_path: str = data.get('raw_dir')

    if not date or not output_path:
        return jsonify({"error": "Missing required fields: date, raw_dir"}), 400

    # 2. Check authentication
    auth_token: Optional[str] = os.environ.get('AUTH_TOKEN')
    if not auth_token:
        return jsonify({"message": "AUTH_TOKEN not set"}), 500

    # 3. Execute business logic
    try:
        service = SalesService(API_BASE_URL)
        result = service.process_sales_data(date, output_path, auth_token)

        return jsonify(result), 201

    except Exception as e:
        return jsonify({
            "error": "Processing failed",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(port=8081)