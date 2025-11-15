"""Business Logic Layer - Sales Data Processing"""
import os
from typing import Dict, Any
from dal.api_client import SalesApiClient
from dal.file_storage import FileStorage


class SalesService:
    """Business logic for fetching and storing sales data"""

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    def process_sales_data(self, date: str, output_path: str, auth_token: str) -> Dict[str, Any]:
        """
        Main business logic: fetch sales data and save to files

        Args:
            date: Date to fetch sales for
            output_path: Directory to save files
            auth_token: API authentication token

        Returns:
            Dictionary with processing results
        """
        # Step 1: Prepare storage
        FileStorage.prepare_directory(output_path)

        # Step 2: Fetch data from API
        api_client = SalesApiClient(self.api_base_url, auth_token)
        pages = api_client.fetch_all_sales(date)

        if not pages:
            return {
                "success": True,
                "message": "No data found",
                "pages_saved": 0,
                "output_path": output_path
            }

        # Step 3: Save to files
        files_saved = FileStorage.save_sales_pages(output_path, date, pages)

        return {
            "success": True,
            "message": f"Data saved to {output_path}",
            "pages_saved": files_saved,
            "output_path": output_path
        }