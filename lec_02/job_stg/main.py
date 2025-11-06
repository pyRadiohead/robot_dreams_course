import os
import fastavro
import shutil
import json
from typing import Tuple, Dict, Any, List
from flask import Flask, request, jsonify, Response

app = Flask(__name__)


@app.route('/', methods=['POST'])
def main() -> Tuple[Response, int]:
    data: Dict[str, Any] = request.json
    raw_dir: str = data['raw_dir']
    stg_dir: str = data['stg_dir']

    if os.path.exists(stg_dir):
        shutil.rmtree(stg_dir)
    os.makedirs(stg_dir, exist_ok=True)

    schema: Dict[str, Any] = {
        'type': 'record',
        'name': 'Sale',
        'fields': [
            {'name': 'client', 'type': 'string'},
            {'name': 'purchase_date', 'type': 'string'},
            {'name': 'product', 'type': 'string'},
            {'name': 'price', 'type': 'int'}
        ]
    }
    json_files: List[str] = [f for f in os.listdir(raw_dir) if f.endswith('.json')]
    for file_name in json_files:
        json_file_path: str = os.path.join(raw_dir, file_name)
        avro_file_path: str = f"{os.path.join(stg_dir, os.path.splitext(file_name)[0])}.avro"
        with open(json_file_path, 'r') as json_file_content:
            json_data: Any = json.load(json_file_content)
            with open(avro_file_path, 'wb') as avro_file:
                fastavro.writer(avro_file, schema, json_data)
    return jsonify({"message": "JSON TO AVRO job finished"}), 201


if __name__ == "__main__":
    app.run(port=8082)
