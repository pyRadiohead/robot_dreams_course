"""Business Logic Layer - JSON to AVRO Conversion"""
import os
import shutil
from typing import Dict, Any
from dal.json_reader import JsonReader
from dal.avro_writer import AvroWriter


class ConversionService:
    """Business logic for converting JSON files to AVRO format"""

    def __init__(self, schema: Dict[str, Any] = None):
        self.schema = schema or AvroWriter.SALES_SCHEMA

    def convert_directory(self, raw_dir: str, stg_dir: str) -> Dict[str, Any]:
        """
        Convert all JSON files in raw_dir to AVRO files in stg_dir

        Args:
            raw_dir: Source directory with JSON files
            stg_dir: Destination directory for AVRO files

        Returns:
            Dictionary with conversion results
        """
        # Step 1: Prepare output directory
        if os.path.exists(stg_dir):
            shutil.rmtree(stg_dir)
        os.makedirs(stg_dir, exist_ok=True)

        # Step 2: Read all JSON files
        json_files_data = JsonReader.read_all_json_files(raw_dir)

        if not json_files_data:
            return {
                "success": True,
                "message": "No JSON files found",
                "files_converted": 0
            }

        # Step 3: Convert each file to AVRO
        converted_count = 0
        for filename, json_data in json_files_data:
            # Generate AVRO filename
            base_name = os.path.splitext(filename)[0]
            avro_filename = f"{base_name}.avro"
            avro_path = os.path.join(stg_dir, avro_filename)

            # Write AVRO file
            AvroWriter.write_avro_file(avro_path, json_data, self.schema)
            converted_count += 1

        return {
            "success": True,
            "message": "JSON TO AVRO job finished",
            "files_converted": converted_count,
            "output_dir": stg_dir
        }