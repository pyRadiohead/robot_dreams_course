# ===== RDS POSTGRESQL FOR DATA WAREHOUSE (GOLD LAYER) =====
# Using RDS PostgreSQL instead of Redshift for cost-effectiveness and simplicity

resource "aws_security_group" "data_warehouse" {
  name_prefix = "${var.project_name}-warehouse-"
  description = "Data Warehouse PostgreSQL SG"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${var.project_name}-warehouse-sg" }
}

resource "aws_db_subnet_group" "warehouse" {
  name       = "${var.project_name}-warehouse-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id, aws_subnet.private_3.id]

  tags = { Name = "${var.project_name}-warehouse-subnet-group" }
}

resource "aws_db_instance" "warehouse" {
  identifier     = "${var.project_name}-warehouse"
  engine         = "postgres"
  engine_version = "15"  # Use major version, AWS will use latest minor version
  instance_class = "db.t3.micro" # Free tier eligible # db.t3.small for better performance than micro

  allocated_storage     = 20  # Free tier: up to 20GB
  max_allocated_storage = 20  # Disable auto-scaling for free tier
  storage_type          = "gp2" # Free tier uses gp2
  storage_encrypted     = false # Free tier doesn't support encryption

  db_name  = "datawarehouse"
  username = "dbadmin" # 'admin' is reserved in PostgreSQL
  password = var.redshift_master_password # Reusing the same variable

  vpc_security_group_ids = [aws_security_group.data_warehouse.id]
  db_subnet_group_name   = aws_db_subnet_group.warehouse.name
  publicly_accessible    = false

  backup_retention_period = 0 # Disable backups for free tier
  skip_final_snapshot     = true
  deletion_protection     = false

  # Performance and monitoring
  performance_insights_enabled = false # Disable to save costs
  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = { Name = "${var.project_name}-warehouse" }
}

# ===== REDSHIFT SERVERLESS (COMMENTED OUT - REQUIRES OPT-IN) =====
# Uncomment these resources once your AWS account has Redshift enabled
#
# resource "aws_security_group" "redshift" {
#   name_prefix = "${var.project_name}-redshift-"
#   description = "Redshift SG"
#   vpc_id      = aws_vpc.main.id
#   tags = { Name = "${var.project_name}-redshift-sg" }
# }
#
# resource "aws_redshiftserverless_namespace" "main" {
#   namespace_name      = "${var.project_name}-namespace"
#   admin_username      = var.redshift_master_username
#   admin_user_password = var.redshift_master_password
#   iam_roles = [
#     aws_iam_role.redshift_glue_access.arn,
#     aws_iam_role.redshift_service.arn,
#   ]
#   tags = { Name = "${var.project_name}-namespace" }
# }
#
# resource "aws_redshiftserverless_workgroup" "main" {
#   workgroup_name       = "${var.project_name}-workgroup"
#   namespace_name       = aws_redshiftserverless_namespace.main.namespace_name
#   base_capacity        = var.redshift_base_capacity
#   publicly_accessible  = false
#   enhanced_vpc_routing = true
#   security_group_ids   = [aws_security_group.redshift.id]
#   subnet_ids = [
#     aws_subnet.private_1.id,
#     aws_subnet.private_2.id,
#     aws_subnet.private_3.id,
#   ]
#   tags = { Name = "${var.project_name}-workgroup" }
# }

# ===== ATHENA WORKGROUP =====
resource "aws_athena_workgroup" "main" {
  name        = "${var.project_name}-workgroup"
  description = "Primary workgroup for data platform"
  state       = "ENABLED"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.id}/query-results/"
    }
    enforce_workgroup_configuration = false
  }

  tags = { Name = "${var.project_name}-athena-workgroup" }
}

