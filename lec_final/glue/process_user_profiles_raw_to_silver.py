"""
AWS Glue ETL Job: Process User Profiles - Raw to Silver
Reads raw user profiles JSONLine data and writes to silver layer as Parquet
Transformations: parse JSON, cast birth_date to DATE
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, trim, to_date
from pyspark.sql.types import DateType

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
SOURCE_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/raw/user_profiles/"
TARGET_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/silver/user_profiles/"

try:
    # Step 1: Read raw user profiles JSONLine data
    # Schema: email, full_name, state, birth_date, phone_number
    print(f"Reading from raw layer: {SOURCE_S3_PATH}")
    raw_user_profiles_df = spark.read.json(SOURCE_S3_PATH)
    
    print(f"Record count: {raw_user_profiles_df.count()}")
    raw_user_profiles_df.printSchema()
    
    # Step 2: Apply transformations
    print("Applying transformations...")
    
    # Clean and cast data types
    df_transformed = raw_user_profiles_df \
        .withColumn("email", trim(col("email"))) \
        .withColumn("full_name", trim(col("full_name"))) \
        .withColumn("state", trim(col("state"))) \
        .withColumn("birth_date", to_date(col("birth_date"), "yyyy-MM-dd")) \
        .withColumn("phone_number", trim(col("phone_number"))) \
        .select("email", "full_name", "state", "birth_date", "phone_number") \
        .filter(
            col("email").isNotNull() & 
            col("birth_date").isNotNull()
        )
    
    print(f"Transformed record count: {df_transformed.count()}")
    df_transformed.printSchema()
    df_transformed.show(5, truncate=False)
    
    # Step 3: Convert to DynamicFrame
    silver_user_profiles_dyf = DynamicFrame.fromDF(df_transformed, glueContext, "silver_user_profiles_dyf")
    
    # Step 4: Write to silver layer as Parquet (no partitioning)
    print(f"Writing to silver layer: {TARGET_S3_PATH}")
    glueContext.write_dynamic_frame.from_options(
        frame=silver_user_profiles_dyf,
        connection_type="s3",
        connection_options={
            "path": TARGET_S3_PATH
        },
        format="parquet",
        transformation_ctx="write_silver_user_profiles"
    )
    
    print("Silver layer write completed successfully")
    
    # Commit the job
    job.commit()
    print("Job completed successfully")

except Exception as e:
    print(f"Error in job execution: {str(e)}")
    raise e

