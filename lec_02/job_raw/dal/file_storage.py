"""Data Access Layer - File System Operations"""
import os
import json
import shutil
from typing import Any, List


class FileStorage:
    """Handles file system operations"""

    @staticmethod
    def prepare_directory(directory_path: str) -> None:
        """
        Prepare directory by removing existing and creating fresh one

        Args:
            directory_path: Path to directory
        """
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)

        os.makedirs(directory_path, exist_ok=True)

    @staticmethod
    def save_json(file_path: str, data: Any) -> None:
        """
        Save data to JSON file

        Args:
            file_path: Full path to file
            data: Data to save (must be JSON serializable)
        """
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def save_sales_pages(output_dir: str, date: str, pages: List[List[Any]]) -> int:
        """
        Save multiple pages of sales data to separate JSON files

        Args:
            output_dir: Directory to save files
            date: Date string for filename
            pages: List of pages to save

        Returns:
            Number of files saved
        """
        for page_num, page_data in enumerate(pages, start=1):
            file_path = os.path.join(output_dir, f'sales_{date}_{page_num}.json')
            FileStorage.save_json(file_path, page_data)

        return len(pages)