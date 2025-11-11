import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs"""
    output_dir = tmp_path / "raw" / "sales" / "2022-08-09"
    return str(output_dir)


@pytest.fixture
def mock_env_token(monkeypatch):
    """Mock the AUTH_TOKEN environment variable"""
    monkeypatch.setenv('AUTH_TOKEN', 'test-token-123')


class TestJobRawMain:
    """Test suite for job_raw main endpoint"""

    def test_missing_auth_token(self, client, temp_output_dir):
        """Test that missing AUTH_TOKEN returns 500 error"""
        # Arrange
        with patch.dict(os.environ, {}, clear=True):
            payload = {
                "date": "2022-08-09",
                "raw_dir": temp_output_dir
            }

            # Act
            response = client.post('/', json=payload)

            # Assert
            assert response.status_code == 500
            assert response.json['message'] == "AUTH_TOKEN not set"

    def test_successful_single_page(self, client, temp_output_dir, mock_env_token):
        """Test successful data fetch with single page"""
        # Arrange
        mock_api_data = [
            {"client": "John", "purchase_date": "2022-08-09", "product": "Book", "price": 100},
            {"client": "Jane", "purchase_date": "2022-08-09", "product": "Pen", "price": 50}
        ]

        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        # Mock the requests.get call
        with patch('main.requests.get') as mock_get:
            # First call returns data, second call returns empty list
            mock_response_1 = Mock()
            mock_response_1.status_code = 200
            mock_response_1.json.return_value = mock_api_data

            mock_response_2 = Mock()
            mock_response_2.status_code = 200
            mock_response_2.json.return_value = []

            mock_get.side_effect = [mock_response_1, mock_response_2]

            # Act
            response = client.post('/', json=payload)

            # Assert
            assert response.status_code == 201
            assert "Data saved to" in response.json['message']

            # Verify API was called with correct parameters
            assert mock_get.call_count == 2
            first_call = mock_get.call_args_list[0]
            assert "date=2022-08-09" in first_call[0][0]
            assert "page=1" in first_call[0][0]
            assert first_call[1]['headers'] == {'Authorization': 'test-token-123'}

            # Verify file was created
            expected_file = os.path.join(temp_output_dir, 'sales_2022-08-09_1.json')
            assert os.path.exists(expected_file)

            # Verify file content
            with open(expected_file, 'r') as f:
                saved_data = json.load(f)
                assert saved_data == mock_api_data

    def test_multiple_pages(self, client, temp_output_dir, mock_env_token):
        """Test pagination - fetching multiple pages"""
        # Arrange
        page_1_data = [{"client": "John", "product": "Book", "price": 100}]
        page_2_data = [{"client": "Jane", "product": "Pen", "price": 50}]
        page_3_data = [{"client": "Bob", "product": "Notebook", "price": 75}]

        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        with patch('main.requests.get') as mock_get:
            # Setup responses for 3 pages + empty response
            responses = []
            for data in [page_1_data, page_2_data, page_3_data]:
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = data
                responses.append(mock_resp)

            # Empty response to stop pagination
            empty_resp = Mock()
            empty_resp.status_code = 200
            empty_resp.json.return_value = []
            responses.append(empty_resp)

            mock_get.side_effect = responses

            # Act
            response = client.post('/', json=payload)

            # Assert
            assert response.status_code == 201
            assert mock_get.call_count == 4

            # Verify all 3 files were created
            for page in [1, 2, 3]:
                file_path = os.path.join(temp_output_dir, f'sales_2022-08-09_{page}.json')
                assert os.path.exists(file_path)

    def test_api_error_stops_processing(self, client, temp_output_dir, mock_env_token):
        """Test that API error (non-200) stops processing"""
        # Arrange
        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        with patch('main.requests.get') as mock_get:
            # First call succeeds, second call fails
            success_resp = Mock()
            success_resp.status_code = 200
            success_resp.json.return_value = [{"client": "John", "product": "Book", "price": 100}]

            error_resp = Mock()
            error_resp.status_code = 500  # API error

            mock_get.side_effect = [success_resp, error_resp]

            # Act
            response = client.post('/', json=payload)

            # Assert
            assert response.status_code == 201  # Job completes even with API error

            # Only first page should be saved
            file_1 = os.path.join(temp_output_dir, 'sales_2022-08-09_1.json')
            file_2 = os.path.join(temp_output_dir, 'sales_2022-08-09_2.json')
            assert os.path.exists(file_1)
            assert not os.path.exists(file_2)

    def test_directory_cleanup(self, client, temp_output_dir, mock_env_token):
        """Test that existing directory is cleaned up before processing"""
        # Arrange - Create existing directory with old file
        os.makedirs(temp_output_dir, exist_ok=True)
        old_file = os.path.join(temp_output_dir, 'old_file.json')
        with open(old_file, 'w') as f:
            json.dump({"old": "data"}, f)

        payload = {
            "date": "2022-08-09",
            "raw_dir": temp_output_dir
        }

        with patch('main.requests.get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = []
            mock_get.return_value = mock_resp

            # Act
            response = client.post('/', json=payload)

            # Assert
            assert response.status_code == 201
            # Old file should be deleted
            assert not os.path.exists(old_file)

    def test_missing_date_field(self, client, temp_output_dir, mock_env_token):
        """Test that missing 'date' field causes error"""
        # Arrange
        payload = {
            "raw_dir": temp_output_dir
            # Missing 'date' field
        }

        # Act & Assert
        with pytest.raises(KeyError):
            client.post('/', json=payload)

    def test_missing_raw_dir_field(self, client, temp_output_dir, mock_env_token):
        """Test that missing 'raw_dir' field causes error"""
        # Arrange
        payload = {
            "date": "2022-08-09"
            # Missing 'raw_dir' field
        }

        # Act & Assert
        with pytest.raises(KeyError):
            client.post('/', json=payload)