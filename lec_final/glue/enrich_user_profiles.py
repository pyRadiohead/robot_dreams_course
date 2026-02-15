"""
AWS Glue ETL Job: Enrich User Profiles - Silver to Gold
Joins silver/customers with silver/user_profiles, enriches data using COALESCE pattern
Writes enriched data to RDS PostgreSQL gold.user_profiles_enriched table
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, coalesce, split, year, current_date, trim, when

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'JDBC_URL', 'JDBC_USER', 'JDBC_PASSWORD'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
CUSTOMERS_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/silver/customers/"
USER_PROFILES_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/silver/user_profiles/"
RDS_CONNECTION_NAME = "yurii-data-platform-warehouse-connection-az1"
# Use public schema (always exists in PostgreSQL) instead of gold schema
TARGET_TABLE = "public.user_profiles_enriched"

# JDBC connection details passed as Glue job parameters (no hardcoded secrets)
JDBC_URL = args['JDBC_URL']
JDBC_USER = args['JDBC_USER']
JDBC_PASSWORD = args['JDBC_PASSWORD']

try:
    # Step 1: Read silver customers data
    print(f"Reading customers from: {CUSTOMERS_S3_PATH}")
    customers_dyf = glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [CUSTOMERS_S3_PATH]},
        format="parquet",
        transformation_ctx="customers_dyf"
    )
    customers_df = customers_dyf.toDF()
    print(f"Customers count: {customers_df.count()}")
    
    # Step 2: Read silver user_profiles data
    print(f"Reading user profiles from: {USER_PROFILES_S3_PATH}")
    user_profiles_dyf = glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [USER_PROFILES_S3_PATH]},
        format="parquet",
        transformation_ctx="user_profiles_dyf"
    )
    user_profiles_df = user_profiles_dyf.toDF()
    print(f"User profiles count: {user_profiles_df.count()}")
    
    # Step 3: Join customers with user_profiles on email (LEFT JOIN)
    print("Joining customers with user profiles...")
    joined_df = customers_df.alias("c").join(
        user_profiles_df.alias("up"),
        col("c.email") == col("up.email"),
        "left"
    )
    
    # Step 4: Apply enrichment logic using COALESCE pattern
    print("Applying enrichment transformations...")
    
    # Split full_name from user_profiles into first and last name
    enriched_df = joined_df.select(
        col("c.client_id"),
        # Use COALESCE to prefer customers data, fill gaps from user_profiles
        coalesce(
            col("c.first_name"),
            when(col("up.full_name").isNotNull(), split(col("up.full_name"), " ").getItem(0))
        ).alias("first_name"),
        coalesce(
            col("c.last_name"),
            when(col("up.full_name").isNotNull(), split(col("up.full_name"), " ").getItem(1))
        ).alias("last_name"),
        col("c.email"),
        col("c.registration_date"),
        # Prefer state from user_profiles (higher quality), fallback to customers
        coalesce(col("up.state"), col("c.state")).alias("state"),
        col("up.birth_date"),
        # Calculate age from birth_date
        when(
            col("up.birth_date").isNotNull(),
            year(current_date()) - year(col("up.birth_date"))
        ).alias("age"),
        col("up.phone_number")
    ).filter(col("client_id").isNotNull())
    
    print(f"Enriched record count: {enriched_df.count()}")
    enriched_df.printSchema()
    enriched_df.show(10, truncate=False)
    
    # Step 5: Write to RDS PostgreSQL using Spark JDBC
    # Using public schema which always exists in PostgreSQL
    print(f"Writing to RDS PostgreSQL: {TARGET_TABLE}")

    enriched_df.write \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("user", JDBC_USER) \
        .option("password", JDBC_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", TARGET_TABLE) \
        .mode("overwrite") \
        .save()
    
    print("Gold layer write completed successfully")
    
    # Commit the job
    job.commit()
    print("Job completed successfully")

except Exception as e:
    print(f"Error in job execution: {str(e)}")
    raise e

