"""
Tests for job_raw Flask application
"""
import os
import sys
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory"""
    output_dir = tmp_path / "raw" / "sales" / "2022-08-09"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


@pytest.fixture
def mock_env_token(monkeypatch):
    """Mock the AUTH_TOKEN environment variable"""
    monkeypatch.setenv("AUTH_TOKEN", "test_token_12345")


class TestJobRawMain:
    """Test suite for job_raw Flask application"""

    def test_missing_auth_token(self, client, temp_output_dir):
        """Test that missing AUTH_TOKEN environment variable returns 500 error"""
        # Arrange
        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        # Act
        with patch.dict(os.environ, {}, clear=True):
            response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert "message" in data or "error" in data

    def test_successful_single_page(self, client, temp_output_dir, mock_env_token):
        """Test successful data fetching from API (single page)"""
        # Arrange
        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        # Mock the requests.get call
        with patch('requests.get') as mock_get:
            # Setup mock response
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = [
                # First page with data
                [
                    {"client": "John Doe", "purchase_date": "2022-08-09", "product": "Laptop", "price": 1200},
                    {"client": "Jane Smith", "purchase_date": "2022-08-09", "product": "Mouse", "price": 25}
                ],
                # Second page empty (stop pagination)
                []
            ]
            mock_get.return_value = mock_resp

            # Act
            response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201
        data = response.get_json()
        assert "message" in data

        # Verify file was created
        json_files = [f for f in os.listdir(temp_output_dir) if f.endswith('.json')]
        assert len(json_files) == 1

        # Verify file content
        with open(os.path.join(temp_output_dir, json_files[0]), 'r') as f:
            saved_data = json.load(f)
            assert len(saved_data) == 2
            assert saved_data[0]["client"] == "John Doe"

        # Verify API was called with correct parameters
        assert mock_get.call_count == 2
        first_call = mock_get.call_args_list[0]
        assert "page=1" in first_call[0][0]

    def test_multiple_pages(self, client, temp_output_dir, mock_env_token):
        """Test pagination - multiple pages of data"""
        # Arrange
        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        with patch('requests.get') as mock_get:
            # Setup responses for 3 pages + empty response
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = [
                [{"client": "User1", "purchase_date": "2022-08-09", "product": "Item1", "price": 100}],  # Page 1
                [{"client": "User2", "purchase_date": "2022-08-09", "product": "Item2", "price": 200}],  # Page 2
                [{"client": "User3", "purchase_date": "2022-08-09", "product": "Item3", "price": 300}],  # Page 3
                []  # Empty page - stop
            ]
            mock_get.return_value = mock_resp

            # Act
            response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201

        # Verify 3 files were created (one per page)
        json_files = [f for f in os.listdir(temp_output_dir) if f.endswith('.json')]
        assert len(json_files) == 3

        # Verify API was called 4 times (3 pages + 1 empty)
        assert mock_get.call_count == 4



    def test_api_error_stops_processing(self, client, temp_output_dir, mock_env_token):
        """Test that API errors are handled gracefully"""
        # Arrange
        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        with patch('requests.get') as mock_get:
            # First call succeeds, second call fails
            mock_resp_success = Mock()
            mock_resp_success.status_code = 200
            mock_resp_success.json.return_value = [{"client": "User1", "purchase_date": "2022-08-09", "product": "Item1", "price": 100}]

            mock_resp_error = Mock()
            mock_resp_error.status_code = 500

            mock_get.side_effect = [mock_resp_success, mock_resp_error]

            # Act
            response = client.post('/', json=payload)

        # Assert - Should still return success for the data that was fetched
        # The exact behavior depends on implementation
        # At minimum, verify that one file was created before the error
        json_files = [f for f in os.listdir(temp_output_dir) if f.endswith('.json')]
        assert len(json_files) >= 1

    def test_directory_cleanup(self, client, temp_output_dir, mock_env_token):
        """Test that existing files in output directory are removed before processing"""
        # Arrange - Create existing file
        old_file = os.path.join(temp_output_dir, "old_file.json")
        with open(old_file, 'w') as f:
            json.dump({"old": "data"}, f)

        assert os.path.exists(old_file)  # Verify old file exists

        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        with patch('requests.get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = [
                [{"client": "New User", "purchase_date": "2022-08-09", "product": "New Item", "price": 500}],
                []
            ]
            mock_get.return_value = mock_resp

            # Act
            response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201
        assert not os.path.exists(old_file)  # Old file should be removed

    def test_missing_date_field(self, client, temp_output_dir, mock_env_token):
        """Test that missing 'date' field returns 400 error"""
        # Arrange
        payload = {
            "raw_dir": temp_output_dir
            # Missing 'date' field
        }

        # Act
        response = client.post('/', json=payload)

        # Assert - Flask will catch the KeyError and return 400
        assert response.status_code == 400

    def test_missing_raw_dir_field(self, client, temp_output_dir, mock_env_token):
        """Test that missing 'raw_dir' field returns 400 error"""
        # Arrange
        payload = {
            "date": "2022-08-09"
            # Missing 'raw_dir' field
        }

        # Act
        response = client.post('/', json=payload)

        # Assert - Flask will catch the KeyError and return 400
        assert response.status_code == 400
