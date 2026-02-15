"""
AWS Glue ETL Job: Process Sales - Bronze to Silver
Reads bronze sales Parquet, applies transformations, writes to silver layer
Transformations: rename columns, clean price, cast types, partition by purchase_date
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, regexp_replace, to_date, trim
from pyspark.sql.types import IntegerType, DecimalType, DateType

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
SOURCE_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/bronze/sales/"
TARGET_S3_PATH = "s3://yurii-data-platform-data-lake-467137831070/silver/sales/"

try:
    # Step 1: Read bronze sales data
    print(f"Reading from bronze layer: {SOURCE_S3_PATH}")
    bronze_sales_dyf = glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [SOURCE_S3_PATH]},
        format="parquet",
        transformation_ctx="bronze_sales_dyf"
    )
    
    print(f"Record count: {bronze_sales_dyf.count()}")
    bronze_sales_dyf.printSchema()
    
    # Step 2: Convert to DataFrame for transformations
    df = bronze_sales_dyf.toDF()
    
    # Step 3: Apply transformations
    print("Applying transformations...")
    
    # Clean and transform data
    df_transformed = df \
        .withColumn("client_id", col("CustomerId").cast(IntegerType())) \
        .withColumn("purchase_date", to_date(col("PurchaseDate"), "yyyy-MM-d")) \
        .withColumn("product_name", trim(col("Product"))) \
        .withColumn("price", 
            regexp_replace(col("Price"), "[$]", "").cast(DecimalType(10, 2))
        ) \
        .select("client_id", "purchase_date", "product_name", "price") \
        .filter(
            col("client_id").isNotNull() & 
            col("purchase_date").isNotNull() & 
            col("product_name").isNotNull() & 
            col("price").isNotNull()
        )
    
    print(f"Transformed record count: {df_transformed.count()}")
    df_transformed.printSchema()
    df_transformed.show(5, truncate=False)
    
    # Step 4: Convert back to DynamicFrame
    silver_sales_dyf = DynamicFrame.fromDF(df_transformed, glueContext, "silver_sales_dyf")
    
    # Step 5: Write to silver layer as Parquet, partitioned by purchase_date
    print(f"Writing to silver layer: {TARGET_S3_PATH}")
    glueContext.write_dynamic_frame.from_options(
        frame=silver_sales_dyf,
        connection_type="s3",
        connection_options={
            "path": TARGET_S3_PATH,
            "partitionKeys": ["purchase_date"]
        },
        format="parquet",
        transformation_ctx="write_silver_sales"
    )
    
    print("Silver layer write completed successfully")
    
    # Commit the job
    job.commit()
    print("Job completed successfully")

except Exception as e:
    print(f"Error in job execution: {str(e)}")
    raise e

