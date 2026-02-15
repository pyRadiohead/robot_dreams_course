variable "project_name" {
  type        = string
  default     = "data-platform"
  description = "Name prefix for all resources"
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for all resources"
}

variable "redshift_master_username" {
  type        = string
  default     = "admin"
  description = "Redshift master username"
}

variable "redshift_master_password" {
  type        = string
  sensitive   = true
  description = "Redshift master password (min 8 chars, must include uppercase, lowercase, and number)"

  validation {
    condition     = length(var.redshift_master_password) >= 8
    error_message = "Password must be at least 8 characters."
  }
}

variable "airflow_admin_username" {
  type        = string
  default     = "admin"
  description = "Airflow admin username"
}

variable "airflow_admin_password" {
  type        = string
  sensitive   = true
  description = "Airflow admin password (min 8 chars)"

  validation {
    condition     = length(var.airflow_admin_password) >= 8
    error_message = "Password must be at least 8 characters."
  }
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC"
}

variable "redshift_base_capacity" {
  type        = number
  default     = 8
  description = "Redshift Serverless base capacity in RPUs (minimum 8)"
}

variable "airflow_cpu" {
  type        = number
  default     = 512
  description = "CPU units for Airflow ECS tasks (256, 512, 1024, 2048, 4096)"
}

variable "airflow_memory" {
  type        = number
  default     = 1024
  description = "Memory (MB) for Airflow ECS tasks"
}

variable "airflow_image" {
  type        = string
  default     = "apache/airflow:2.8.1"
  description = "Docker image for Airflow"
}

variable "airflow_db_instance_class" {
  type        = string
  default     = "db.t3.micro"
  description = "RDS instance class for Airflow metadata DB (db.t3.micro is free-tier eligible)"
}

variable "airflow_db_allocated_storage" {
  type        = number
  default     = 20
  description = "Allocated storage in GB for Airflow metadata DB"
}

variable "airflow_fernet_key" {
  type        = string
  default     = "YlCImzjge_TeZc8jGyCNFAeET9hGIkUEBF2xYE4UeXo="
  description = "Fernet key for Airflow encryption"
}

variable "airflow_webserver_secret_key" {
  type        = string
  default     = "d2def9c5d35ac1a02f112e080f2b130c27323da0dda21f9a1f875428cd6f"
  description = "Secret key for Airflow webserver"
}

variable "log_retention_days" {
  type        = number
  default     = 7
  description = "CloudWatch log retention in days (reduced from 14 to save costs)"
}

