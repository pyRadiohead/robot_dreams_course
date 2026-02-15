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

output "redshift_endpoint" {
  description = "Redshift Serverless Workgroup Endpoint"
  value       = aws_redshiftserverless_workgroup.main.endpoint[0].address
}

output "redshift_workgroup_name" {
  description = "Redshift Serverless Workgroup Name"
  value       = aws_redshiftserverless_workgroup.main.workgroup_name
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

