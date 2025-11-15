"""Data Access Layer - JSON File Reading"""
import os
import json
from typing import List, Dict, Any, Tuple


class JsonReader:
    """Handles reading JSON files"""

    @staticmethod
    def list_json_files(directory: str) -> List[str]:
        """
        List all JSON files in directory

        Args:
            directory: Path to directory

        Returns:
            List of JSON filenames
        """
        if not os.path.exists(directory):
            return []

        return [f for f in os.listdir(directory) if f.endswith('.json')]

    @staticmethod
    def read_json_file(file_path: str) -> Any:
        """
        Read and parse JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def read_all_json_files(directory: str) -> List[Tuple[str, Any]]:
        """
        Read all JSON files from directory

        Args:
            directory: Path to directory

        Returns:
            List of tuples (filename, data)
        """
        json_files = JsonReader.list_json_files(directory)
        results = []

        for filename in json_files:
            file_path = os.path.join(directory, filename)
            data = JsonReader.read_json_file(file_path)
            results.append((filename, data))

        return results