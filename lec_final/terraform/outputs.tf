output "data_lake_bucket_name" {
  description = "S3 Data Lake Bucket Name"
  value       = aws_s3_bucket.data_lake.id
}

output "airflow_bucket_name" {
  description = "S3 Airflow Bucket Name"
  value       = aws_s3_bucket.airflow.id
}

output "athena_bucket_name" {
  description = "S3 Athena Results Bucket Name"
  value       = aws_s3_bucket.athena_results.id
}

output "glue_database_name" {
  description = "Glue Database Name"
  value       = aws_glue_catalog_database.main.name
}

output "glue_crawler_name" {
  description = "Glue S3 Crawler Name (use with: aws glue start-crawler --name <this>)"
  value       = aws_glue_crawler.s3_crawler.name
}

output "warehouse_endpoint" {
  description = "Data Warehouse (RDS PostgreSQL) Endpoint"
  value       = aws_db_instance.warehouse.endpoint
}

output "warehouse_database_name" {
  description = "Data Warehouse Database Name"
  value       = aws_db_instance.warehouse.db_name
}

output "warehouse_crawler_name" {
  description = "Glue Warehouse Crawler Name"
  value       = aws_glue_crawler.warehouse_crawler.name
}

output "airflow_web_ui" {
  description = "Airflow Web UI URL"
  value       = "http://${aws_lb.airflow.dns_name}"
}

output "athena_workgroup_name" {
  description = "Athena WorkGroup Name"
  value       = aws_athena_workgroup.main.name
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

