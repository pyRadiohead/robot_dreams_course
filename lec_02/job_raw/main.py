import os
import requests
import json
import shutil
from typing import Tuple, Dict, Any, Optional
from flask import Flask, request, jsonify, Response

app = Flask(__name__)


@app.route('/', methods=['POST'])
def main() -> Tuple[Response, int]:
    data: Dict[str, Any] = request.json
    date: str = data['date']
    output_path: str = data['raw_dir']

    # deleting folder if exists
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    # Recreating folders
    os.makedirs(output_path, exist_ok=True)
    auth_token: Optional[str] = os.environ.get('AUTH_TOKEN')
    if not auth_token:
        return jsonify({"message": "AUTH_TOKEN not set"}), 500
    headers: Dict[str, str] = {'Authorization': auth_token}
    page: int = 1
    while True:
        api_url: str = f"https://fake-api-vycpfa6oca-uc.a.run.app/sales?date={date}&page={page}"
        response: requests.Response = requests.get(api_url, headers=headers)

        if response.status_code != 200:
            # Обробити помилку
            break

        api_data: Any = response.json()

        if not api_data:
            # Даних більше немає, виходимо з циклу
            break

        # Зберігаємо "сторінку" в окремий файл
        file_path: str = os.path.join(output_path, f'sales_{date}_{page}.json')
        with open(file_path, 'w') as f:
            json.dump(api_data, f)

        page += 1

    return jsonify({"message": f"Data saved to {output_path}"}), 201


if __name__ == "__main__":
    app.run(port=8081)
