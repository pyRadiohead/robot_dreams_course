"""
AWS Glue ETL Job: Process Customers - Bronze to Silver
Reads bronze customers Parquet, applies transformations, writes to silver layer
Transformations: rename columns, deduplicate, cast types
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, trim, to_date, row_number
from pyspark.sql.types import IntegerType, DateType
from pyspark.sql.window import Window

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
SOURCE_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/bronze/customers/"
TARGET_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/silver/customers/"

try:
    # Step 1: Read bronze customers data
    print(f"Reading from bronze layer: {SOURCE_S3_PATH}")
    bronze_customers_dyf = glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [SOURCE_S3_PATH]},
        format="parquet",
        transformation_ctx="bronze_customers_dyf"
    )
    
    print(f"Record count: {bronze_customers_dyf.count()}")
    bronze_customers_dyf.printSchema()
    
    # Step 2: Convert to DataFrame for transformations
    df = bronze_customers_dyf.toDF()
    
    # Step 3: Apply transformations
    print("Applying transformations...")
    
    # Rename columns and cast types
    df_transformed = df \
        .withColumn("client_id", col("Id").cast(IntegerType())) \
        .withColumn("first_name", trim(col("FirstName"))) \
        .withColumn("last_name", trim(col("LastName"))) \
        .withColumn("email", trim(col("Email"))) \
        .withColumn("registration_date", to_date(col("RegistrationDate"), "yyyy-MM-d")) \
        .withColumn("state", trim(col("State"))) \
        .select("client_id", "first_name", "last_name", "email", "registration_date", "state")
    
    # Step 4: Deduplicate by client_id (keep latest record based on registration_date)
    # Each day's dump contains all previous data, so we need to keep only unique records
    print("Deduplicating records...")
    window_spec = Window.partitionBy("client_id").orderBy(col("registration_date").desc())
    
    df_deduped = df_transformed \
        .withColumn("row_num", row_number().over(window_spec)) \
        .filter(col("row_num") == 1) \
        .drop("row_num") \
        .filter(col("client_id").isNotNull() & col("email").isNotNull())
    
    print(f"Deduplicated record count: {df_deduped.count()}")
    df_deduped.printSchema()
    df_deduped.show(5, truncate=False)
    
    # Step 5: Convert back to DynamicFrame
    silver_customers_dyf = DynamicFrame.fromDF(df_deduped, glueContext, "silver_customers_dyf")
    
    # Step 6: Write to silver layer as Parquet (no partitioning)
    print(f"Writing to silver layer: {TARGET_S3_PATH}")
    glueContext.write_dynamic_frame.from_options(
        frame=silver_customers_dyf,
        connection_type="s3",
        connection_options={
            "path": TARGET_S3_PATH
        },
        format="parquet",
        transformation_ctx="write_silver_customers"
    )
    
    print("Silver layer write completed successfully")
    
    # Commit the job
    job.commit()
    print("Job completed successfully")

except Exception as e:
    print(f"Error in job execution: {str(e)}")
    raise e

