"""
Tests for job_stg Flask application
"""
import os
import sys
import json
import pytest
import fastavro
from unittest.mock import Mock, patch

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
def temp_raw_dir(tmp_path):
    """Create a temporary directory for raw JSON files"""
    raw_dir = tmp_path / "raw" / "sales" / "2022-08-09"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return str(raw_dir)


@pytest.fixture
def temp_stg_dir(tmp_path):
    """Create a temporary directory for staging AVRO files"""
    stg_dir = tmp_path / "stg" / "sales" / "2022-08-09"
    return str(stg_dir)


@pytest.fixture
def sample_sales_data():
    """Sample sales data for testing"""
    return [
        {
            "client": "John Doe",
            "purchase_date": "2022-08-09",
            "product": "Laptop",
            "price": 1200
        },
        {
            "client": "Jane Smith",
            "purchase_date": "2022-08-09",
            "product": "Mouse",
            "price": 25
        }
    ]


@pytest.fixture
def create_json_files(temp_raw_dir, sample_sales_data):
    """Create sample JSON files in raw directory"""
    def _create_files(num_files=1, data=None):
        if data is None:
            data = sample_sales_data

        files_created = []
        for i in range(1, num_files + 1):
            file_path = os.path.join(temp_raw_dir, f'sales_2022-08-09_{i}.json')
            with open(file_path, 'w') as f:
                json.dump(data, f)
            files_created.append(file_path)

        return files_created

    return _create_files


class TestJobStgMain:
    """Test suite for job_stg main endpoint"""

    def test_successful_single_file_conversion(self, client, temp_raw_dir, temp_stg_dir,
                                               create_json_files, sample_sales_data):
        """Test successful conversion of single JSON file to AVRO"""
        # Arrange
        create_json_files(num_files=1)

        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        if response.status_code != 201:
            print(f"Response: {response.get_json()}")
        assert response.status_code == 201
        assert "JSON TO AVRO job finished" in response.json['message']

        # Verify AVRO file was created
        avro_file = os.path.join(temp_stg_dir, 'sales_2022-08-09_1.avro')
        assert os.path.exists(avro_file)

        # Verify AVRO file content
        with open(avro_file, 'rb') as f:
            reader = fastavro.reader(f)
            avro_data = list(reader)
            assert avro_data == sample_sales_data


    def test_multiple_files_conversion(self, client, temp_raw_dir, temp_stg_dir,
                                      create_json_files, sample_sales_data):
        """Test conversion of multiple JSON files to AVRO"""
        # Arrange
        num_files = 3
        create_json_files(num_files=num_files)

        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201

        # Verify all AVRO files were created
        for i in range(1, num_files + 1):
            avro_file = os.path.join(temp_stg_dir, f'sales_2022-08-09_{i}.avro')
            assert os.path.exists(avro_file)

            # Verify content
            with open(avro_file, 'rb') as f:
                reader = fastavro.reader(f)
                avro_data = list(reader)
                assert avro_data == sample_sales_data


    def test_empty_raw_directory(self, client, temp_raw_dir, temp_stg_dir):
        """Test handling when raw directory has no JSON files"""
        # Arrange - raw_dir exists but is empty
        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201

        # Verify stg_dir was created but is empty
        assert os.path.exists(temp_stg_dir)
        files = os.listdir(temp_stg_dir)
        avro_files = [f for f in files if f.endswith('.avro')]
        assert len(avro_files) == 0


    def test_directory_cleanup(self, client, temp_raw_dir, temp_stg_dir, create_json_files):
        """Test that existing stg directory is cleaned up before processing"""
        # Arrange - Create existing stg directory with old file
        os.makedirs(temp_stg_dir, exist_ok=True)
        old_file = os.path.join(temp_stg_dir, 'old_file.avro')
        with open(old_file, 'wb') as f:
            f.write(b'old data')

        assert os.path.exists(old_file)  # Verify old file exists

        # Create new JSON files
        create_json_files(num_files=1)

        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201
        # Old file should be deleted
        assert not os.path.exists(old_file)
        # New file should exist
        new_file = os.path.join(temp_stg_dir, 'sales_2022-08-09_1.avro')
        assert os.path.exists(new_file)


    def test_avro_schema_validation(self, client, temp_raw_dir, temp_stg_dir, create_json_files):
        """Test that AVRO files have correct schema with decimal price"""
        # Arrange
        create_json_files(num_files=1)

        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201

        # Verify schema
        avro_file = os.path.join(temp_stg_dir, 'sales_2022-08-09_1.avro')
        with open(avro_file, 'rb') as f:
            reader = fastavro.reader(f)
            schema = reader.writer_schema

            # Verify schema structure
            assert schema['type'] == 'record'
            assert schema['name'] == 'Sale'

            # Verify fields
            fields = {field['name']: field for field in schema['fields']}
            assert 'client' in fields
            assert 'purchase_date' in fields
            assert 'product' in fields
            assert 'price' in fields

            # Verify field types
            assert fields['client']['type'] == 'string'
            assert fields['purchase_date']['type'] == 'string'
            assert fields['product']['type'] == 'string'

            # Verify price is int type
            price_field = fields['price']
            assert price_field['type'] == 'int'


    def test_missing_raw_dir_field(self, client, temp_stg_dir):
        """Test that missing 'raw_dir' field returns 400 error"""
        # Arrange
        payload = {
            "stg_dir": temp_stg_dir
            # Missing 'raw_dir' field
        }

        # Act
        response = client.post('/', json=payload)

        # Assert - Flask will return 400 for missing fields
        assert response.status_code == 400
        assert "error" in response.get_json()


    def test_missing_stg_dir_field(self, client, temp_raw_dir):
        """Test that missing 'stg_dir' field returns 400 error"""
        # Arrange
        payload = {
            "raw_dir": temp_raw_dir
            # Missing 'stg_dir' field
        }

        # Act
        response = client.post('/', json=payload)

        # Assert - Flask will return 400 for missing fields
        assert response.status_code == 400
        assert "error" in response.get_json()


    def test_non_json_files_ignored(self, client, temp_raw_dir, temp_stg_dir, create_json_files):
        """Test that non-JSON files in raw directory are ignored"""
        # Arrange
        create_json_files(num_files=1)

        # Create non-JSON files
        txt_file = os.path.join(temp_raw_dir, 'readme.txt')
        with open(txt_file, 'w') as f:
            f.write('This is a text file')

        csv_file = os.path.join(temp_raw_dir, 'data.csv')
        with open(csv_file, 'w') as f:
            f.write('col1,col2\nval1,val2')

        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201

        # Only JSON file should be converted
        avro_files = [f for f in os.listdir(temp_stg_dir) if f.endswith('.avro')]
        assert len(avro_files) == 1
        assert avro_files[0] == 'sales_2022-08-09_1.avro'


    def test_different_data_types(self, client, temp_raw_dir, temp_stg_dir):
        """Test conversion with different data values"""
        # Arrange
        varied_data = [
            {
                "client": "Alice",
                "purchase_date": "2022-01-01",
                "product": "Product A",
                "price": 0
            },
            {
                "client": "Bob",
                "purchase_date": "2022-12-31",
                "product": "Product B",
                "price": 999999
            }
        ]

        json_file = os.path.join(temp_raw_dir, 'sales_2022-08-09_1.json')
        with open(json_file, 'w') as f:
            json.dump(varied_data, f)

        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201

        # Verify data integrity
        avro_file = os.path.join(temp_stg_dir, 'sales_2022-08-09_1.avro')
        with open(avro_file, 'rb') as f:
            reader = fastavro.reader(f)
            avro_data = list(reader)
            assert avro_data == varied_data


    def test_preserves_filename_structure(self, client, temp_raw_dir, temp_stg_dir):
        """Test that AVRO files preserve the original JSON filename structure"""
        # Arrange
        test_filenames = [
            'sales_2022-08-09_1.json',
            'sales_2022-08-09_2.json',
            'sales_2023-01-01_1.json'
        ]

        for filename in test_filenames:
            file_path = os.path.join(temp_raw_dir, filename)
            with open(file_path, 'w') as f:
                json.dump([{"client": "Test", "purchase_date": "2022-08-09",
                           "product": "Item", "price": 100}], f)

        payload = {
            "raw_dir": temp_raw_dir,
            "stg_dir": temp_stg_dir
        }

        # Act
        response = client.post('/', json=payload)

        # Assert
        assert response.status_code == 201

        # Verify corresponding AVRO files exist
        expected_avro_files = [
            'sales_2022-08-09_1.avro',
            'sales_2022-08-09_2.avro',
            'sales_2023-01-01_1.avro'
        ]

        for avro_filename in expected_avro_files:
            avro_path = os.path.join(temp_stg_dir, avro_filename)
            assert os.path.exists(avro_path)


