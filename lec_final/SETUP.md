# Setup Guide for lec_final Project

## Prerequisites

- Python 3.11 or higher
- AWS CLI configured with appropriate credentials
- Access to AWS services (S3, Glue, RDS, MWAA)

## Virtual Environment Setup

### 1. Create Virtual Environment

```bash
cd lec_final
python3 -m venv .venv
```

### 2. Activate Virtual Environment

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Package Overview

### Core Components

| Package | Version | Purpose |
|---------|---------|---------|
| `apache-airflow` | 2.8.1 | Workflow orchestration |
| `apache-airflow-providers-amazon` | 8.16.0 | AWS operators (Glue, S3, Redshift) |
| `apache-airflow-providers-apache-spark` | 4.7.1 | Spark operators |
| `boto3` | 1.34.51 | AWS SDK for Python |
| `pyspark` | 3.5.0 | Distributed data processing |
| `psycopg2-binary` | 2.9.9 | PostgreSQL driver for RDS |
| `pandas` | 2.2.0 | Data manipulation |
| `pyarrow` | 15.0.0 | Parquet file support |

## Environment-Specific Notes

### AWS Glue Environment

When running Glue jobs in AWS Glue, the following packages are **pre-installed**:
- `awsglue` (AWS Glue libraries)
- `pyspark` (specific version managed by AWS)
- `boto3`

**You do NOT need to install these in AWS Glue.** The `requirements.txt` is primarily for:
1. Local development and testing
2. Running Spark jobs locally
3. Developing and testing Airflow DAGs locally

### AWS MWAA (Managed Airflow)

For AWS MWAA, you need to create a separate `requirements.txt` with only Airflow-compatible packages:

```txt
# requirements-mwaa.txt
apache-airflow-providers-amazon==8.16.0
apache-airflow-providers-apache-spark==4.7.1
boto3==1.34.51
psycopg2-binary==2.9.9
pandas==2.2.0
pyarrow==15.0.0
```

Upload this to your Airflow S3 bucket and configure MWAA to use it.

### Local Spark Development

For local Spark development, ensure you have Java 11 or 17 installed:

```bash
# Check Java version
java -version

# If not installed, install Java (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install openjdk-11-jdk

# Set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
```

## Testing the Setup

### Test Spark Installation

```bash
python -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.appName('test').getOrCreate(); print('Spark version:', spark.version); spark.stop()"
```

### Test AWS Connection

```bash
python -c "import boto3; s3 = boto3.client('s3'); print('AWS connection successful')"
```

### Test PostgreSQL Driver

```bash
python -c "import psycopg2; print('psycopg2 version:', psycopg2.__version__)"
```

## Running the Project

### 1. Local Spark Job

```bash
cd spark_standalone
python spark_job.py
```

### 2. Local Airflow (for DAG development)

```bash
# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start Airflow webserver
airflow webserver --port 8080

# In another terminal, start scheduler
airflow scheduler
```

### 3. Deploy to AWS

See `IMPLEMENTATION_PLAN.md` for detailed deployment instructions.

## Troubleshooting

### Issue: `awsglue` module not found

**Solution**: The `awsglue` module is only available in AWS Glue environment. For local development:
- Comment out `awsglue` imports when testing locally
- Use PySpark directly for local testing
- Deploy to AWS Glue for actual execution

### Issue: Airflow installation conflicts

**Solution**: Use constraints file for Airflow:
```bash
pip install "apache-airflow==2.8.1" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.11.txt"
```

### Issue: PostgreSQL connection errors

**Solution**: Ensure RDS security group allows inbound connections from your IP.

## Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

