# ===== GLUE SERVICE ROLE =====
resource "aws_iam_role" "glue_service" {
  name = "${var.project_name}-glue-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service_managed" {
  role       = aws_iam_role.glue_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_access" {
  name = "GlueS3Access"
  role = aws_iam_role.glue_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
      Resource = [
        aws_s3_bucket.data_lake.arn,
        "${aws_s3_bucket.data_lake.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "glue_redshift_access" {
  name = "GlueRedshiftAccess"
  role = aws_iam_role.glue_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["redshift-serverless:*"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeRouteTables",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcEndpoints",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "glue_secrets_manager" {
  name = "GlueSecretsManagerFullAccess"
  role = aws_iam_role.glue_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:*"]
      Resource = "*"
    }]
  })
}

# ===== REDSHIFT GLUE ACCESS ROLE =====
resource "aws_iam_role" "redshift_glue_access" {
  name = "${var.project_name}-redshift-glue-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = ["redshift.amazonaws.com", "redshift-serverless.amazonaws.com"] }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "redshift_glue_catalog" {
  name = "GlueCatalogAccess"
  role = aws_iam_role.redshift_glue_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions", "glue:GetTables", "glue:GetDatabases"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy" "redshift_secrets_manager" {
  name = "RedshiftSecretsManagerFullAccess"
  role = aws_iam_role.redshift_glue_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:*"]
      Resource = "*"
    }]
  })
}

