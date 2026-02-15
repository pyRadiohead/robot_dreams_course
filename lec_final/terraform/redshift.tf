# ===== REDSHIFT SECURITY GROUP =====
resource "aws_security_group" "redshift" {
  name_prefix = "${var.project_name}-redshift-"
  description = "Redshift SG"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${var.project_name}-redshift-sg" }
}

# ===== REDSHIFT SERVERLESS =====
resource "aws_redshiftserverless_namespace" "main" {
  namespace_name      = "${var.project_name}-namespace"
  admin_username      = var.redshift_master_username
  admin_user_password = var.redshift_master_password

  iam_roles = [
    aws_iam_role.redshift_glue_access.arn,
    aws_iam_role.redshift_service.arn,
  ]

  tags = { Name = "${var.project_name}-namespace" }
}

resource "aws_redshiftserverless_workgroup" "main" {
  workgroup_name     = "${var.project_name}-workgroup"
  namespace_name     = aws_redshiftserverless_namespace.main.namespace_name
  base_capacity      = var.redshift_base_capacity # 8 RPUs = minimum, ~$0.375/hr when active
  publicly_accessible = false
  enhanced_vpc_routing = true

  security_group_ids = [aws_security_group.redshift.id]

  subnet_ids = [
    aws_subnet.private_1.id,
    aws_subnet.private_2.id,
    aws_subnet.private_3.id,
  ]

  tags = { Name = "${var.project_name}-workgroup" }
}

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

