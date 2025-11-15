"""Data Access Layer - AVRO File Writing"""
import os
import fastavro
from typing import Dict, Any, List


class AvroWriter:
    """Handles writing AVRO files"""

    SALES_SCHEMA = {
        'type': 'record',
        'name': 'Sale',
        'fields': [
            {'name': 'client', 'type': 'string'},
            {'name': 'purchase_date', 'type': 'string'},
            {'name': 'product', 'type': 'string'},
            {'name': 'price', 'type': 'int'}
        ]
    }

    @staticmethod
    def write_avro_file(file_path: str, data: List[Dict[str, Any]],
                        schema: Dict[str, Any] = None) -> None:
        """
        Write data to AVRO file

        Args:
            file_path: Path to output file
            data: List of records to write
            schema: AVRO schema (uses default if None)
        """
        if schema is None:
            schema = AvroWriter.SALES_SCHEMA

        with open(file_path, 'wb') as avro_file:
            fastavro.writer(avro_file, schema, data)

    @staticmethod
    def convert_json_to_avro(json_file_path: str, avro_file_path: str,
                             json_data: Any, schema: Dict[str, Any] = None) -> None:
        """
        Convert JSON data to AVRO format

        Args:
            json_file_path: Source JSON file path (for reference)
            avro_file_path: Destination AVRO file path
            json_data: Parsed JSON data
            schema: AVRO schema
        """
        AvroWriter.write_avro_file(avro_file_path, json_data, schema)