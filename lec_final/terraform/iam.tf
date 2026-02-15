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

resource "aws_iam_role_policy" "glue_network_access" {
  name = "GlueNetworkAccess"
  role = aws_iam_role.glue_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
          "ec2:DescribeVpcs",
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
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

# ===== REDSHIFT SERVICE ROLE =====
resource "aws_iam_role" "redshift_service" {
  name = "${var.project_name}-redshift-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = ["redshift.amazonaws.com", "redshift-serverless.amazonaws.com"] }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "redshift_s3_access" {
  name = "RedshiftS3Access"
  role = aws_iam_role.redshift_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion", "s3:ListBucket", "s3:GetBucketLocation"]
        Resource = [aws_s3_bucket.data_lake.arn, "${aws_s3_bucket.data_lake.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "redshift_glue_data_catalog" {
  name = "RedshiftGlueDataCatalogAccess"
  role = aws_iam_role.redshift_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["glue:*"]
      Resource = [
        "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
        "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/awsdatacatalog",
        "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/*",
        "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/*/*"
      ]
    }]
  })
}

# ===== DATA CATALOG USER ROLE =====
resource "aws_iam_role" "datacatalog_user" {
  name = "${var.project_name}-datacatalog-user-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "datacatalog_access" {
  name = "RedshiftDataCatalogAccess"
  role = aws_iam_role.datacatalog_user.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "redshift-serverless:GetCredentials",
        "redshift-serverless:GetWorkgroup",
        "redshift-serverless:GetNamespace",
        "redshift-data:*",
        "glue:GetDatabase", "glue:GetDatabases",
        "glue:GetTable", "glue:GetTables",
        "glue:GetPartition", "glue:GetPartitions",
        "glue:BatchGetPartition", "glue:SearchTables",
        "glue:GetCatalogImportStatus",
        "glue:GetDataCatalogEncryptionSettings"
      ]
      Resource = "*"
    }]
  })
}


# ===== AIRFLOW EXECUTION ROLE (ECS) =====
resource "aws_iam_role" "airflow_execution" {
  name = "${var.project_name}-airflow-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "airflow_execution_managed" {
  role       = aws_iam_role.airflow_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "airflow_execution_access" {
  name = "AirflowGlueAccess"
  role = aws_iam_role.airflow_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["glue:*", "s3:*", "athena:*", "redshift:*", "logs:*"]
      Resource = "*"
    }]
  })
}

# ===== AIRFLOW TASK ROLE =====
resource "aws_iam_role" "airflow_task" {
  name = "${var.project_name}-airflow-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "airflow_task_access" {
  name = "AirflowDataPlatformAccess"
  role = aws_iam_role.airflow_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["glue:*", "s3:*", "athena:*", "redshift:*", "logs:*", "ecs:*"]
      Resource = "*"
    }]
  })
}

# ===== DAG SYNC TASK ROLE =====
resource "aws_iam_role" "dag_sync_task" {
  name = "${var.project_name}-dag-sync-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "dag_sync_s3_access" {
  name = "DAGSyncS3Access"
  role = aws_iam_role.dag_sync_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.airflow.arn, "${aws_s3_bucket.airflow.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      }
    ]
  })
}

# ===== EVENTBRIDGE EXECUTION ROLE =====
resource "aws_iam_role" "eventbridge_execution" {
  name = "${var.project_name}-eventbridge-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_ecs_access" {
  name = "EventBridgeECSAccess"
  role = aws_iam_role.eventbridge_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:RunTask"]
        Resource = aws_ecs_task_definition.dag_sync.arn
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = [aws_iam_role.airflow_execution.arn, aws_iam_role.dag_sync_task.arn]
      }
    ]
  })
}