"""Data Access Layer - API Communication"""
import requests
from typing import Optional, List, Dict, Any


class SalesApiClient:
    """Handles communication with the sales API"""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {'Authorization': auth_token}

    def fetch_sales_page(self, date: str, page: int) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch a single page of sales data from the API

        Args:
            date: Date in format YYYY-MM-DD
            page: Page number to fetch

        Returns:
            List of sales records or None if error/no data
        """
        api_url = f"{self.base_url}/sales?date={date}&page={page}"

        try:
            response = requests.get(api_url, headers=self.headers)

            if response.status_code != 200:
                return None

            data = response.json()
            return data if data else None

        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def fetch_all_sales(self, date: str) -> List[List[Dict[str, Any]]]:
        """
        Fetch all pages of sales data for a given date

        Args:
            date: Date in format YYYY-MM-DD

        Returns:
            List of pages, where each page is a list of sales records
        """
        all_pages = []
        page = 1

        while True:
            page_data = self.fetch_sales_page(date, page)

            if page_data is None:
                break

            all_pages.append(page_data)
            page += 1

        return all_pages
