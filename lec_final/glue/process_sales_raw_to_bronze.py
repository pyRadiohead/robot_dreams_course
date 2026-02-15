"""
AWS Glue ETL Job: Process Sales - Raw to Bronze
Reads raw sales CSV data from Glue Catalog and writes to bronze layer as Parquet
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
DATABASE_NAME = "yurii_data_platform_database"
SOURCE_TABLE = "sales"
TARGET_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/bronze/sales/"

try:
    # Step 1: Read raw sales data from Glue Catalog
    # Schema: CustomerId, PurchaseDate, Product, Price (all STRING)
    print(f"Reading from Glue Catalog: {DATABASE_NAME}.{SOURCE_TABLE}")
    raw_sales_dyf = glueContext.create_dynamic_frame.from_catalog(
        database=DATABASE_NAME,
        table_name=SOURCE_TABLE,
        transformation_ctx="raw_sales_dyf"
    )
    
    print(f"Record count: {raw_sales_dyf.count()}")
    raw_sales_dyf.printSchema()
    
    # Step 2: Write to bronze layer as Parquet
    # Keep all fields as STRING, preserve original column names
    # Partition by the date folder structure from source
    print(f"Writing to bronze layer: {TARGET_S3_PATH}")
    glueContext.write_dynamic_frame.from_options(
        frame=raw_sales_dyf,
        connection_type="s3",
        connection_options={
            "path": TARGET_S3_PATH,
            "partitionKeys": []  # Data already partitioned by folder structure
        },
        format="parquet",
        transformation_ctx="write_bronze_sales"
    )
    
    print("Bronze layer write completed successfully")
    
    # Commit the job
    job.commit()
    print("Job completed successfully")

except Exception as e:
    print(f"Error in job execution: {str(e)}")
    raise e

