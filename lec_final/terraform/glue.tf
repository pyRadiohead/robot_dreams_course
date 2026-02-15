# ===== GLUE DATABASE =====
resource "aws_glue_catalog_database" "main" {
  name        = "${replace(var.project_name, "-", "_")}_database"
  description = "Main database for data platform"
}

# ===== GLUE CRAWLER SECURITY GROUP =====
resource "aws_security_group" "glue_crawler" {
  name_prefix = "${var.project_name}-glue-crawler-"
  description = "Glue Crawler SG"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-glue-crawler-sg" }
}

# ===== S3 CRAWLER =====
resource "aws_glue_crawler" "s3_crawler" {
  name          = "${var.project_name}-s3-crawler"
  role          = aws_iam_role.glue_service.arn
  database_name = aws_glue_catalog_database.main.name

  s3_target {
    path       = "s3://${aws_s3_bucket.data_lake.id}/raw/"
    exclusions = ["**/_temporary/**", "**/.spark-staging/**", "**/.DS_Store/**"]
  }

  s3_target {
    path       = "s3://${aws_s3_bucket.data_lake.id}/bronze/"
    exclusions = ["**/_temporary/**", "**/.spark-staging/**"]
  }

  s3_target {
    path       = "s3://${aws_s3_bucket.data_lake.id}/silver/"
    exclusions = ["**/_temporary/**", "**/.spark-staging/**"]
  }

  s3_target {
    path       = "s3://${aws_s3_bucket.data_lake.id}/gold/"
    exclusions = ["**/_temporary/**", "**/.spark-staging/**"]
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
  })
}

# ===== GLUE CONNECTIONS TO DATA WAREHOUSE (RDS PostgreSQL) =====
resource "aws_glue_connection" "warehouse_az1" {
  name            = "${var.project_name}-warehouse-connection-az1"
  connection_type = "JDBC"

  connection_properties = {
    JDBC_CONNECTION_URL = "jdbc:postgresql://${aws_db_instance.warehouse.endpoint}/datawarehouse"
    USERNAME            = "dbadmin"
    PASSWORD            = var.redshift_master_password
  }

  physical_connection_requirements {
    security_group_id_list = [aws_security_group.glue_crawler.id]
    subnet_id              = aws_subnet.private_1.id
    availability_zone      = aws_subnet.private_1.availability_zone
  }
}

resource "aws_glue_connection" "warehouse_az2" {
  name            = "${var.project_name}-warehouse-connection-az2"
  connection_type = "JDBC"

  connection_properties = {
    JDBC_CONNECTION_URL = "jdbc:postgresql://${aws_db_instance.warehouse.endpoint}/datawarehouse"
    USERNAME            = "dbadmin"
    PASSWORD            = var.redshift_master_password
  }

  physical_connection_requirements {
    security_group_id_list = [aws_security_group.glue_crawler.id]
    subnet_id              = aws_subnet.private_2.id
    availability_zone      = aws_subnet.private_2.availability_zone
  }
}

resource "aws_glue_connection" "warehouse_az3" {
  name            = "${var.project_name}-warehouse-connection-az3"
  connection_type = "JDBC"

  connection_properties = {
    JDBC_CONNECTION_URL = "jdbc:postgresql://${aws_db_instance.warehouse.endpoint}/datawarehouse"
    USERNAME            = "dbadmin"
    PASSWORD            = var.redshift_master_password
  }

  physical_connection_requirements {
    security_group_id_list = [aws_security_group.glue_crawler.id]
    subnet_id              = aws_subnet.private_3.id
    availability_zone      = aws_subnet.private_3.availability_zone
  }
}

# ===== DATA WAREHOUSE CRAWLER =====
resource "aws_glue_crawler" "warehouse_crawler" {
  name          = "${var.project_name}-warehouse-crawler"
  role          = aws_iam_role.glue_service.arn
  database_name = aws_glue_catalog_database.main.name

  jdbc_target {
    connection_name = aws_glue_connection.warehouse_az1.name
    path            = "datawarehouse/%"
    exclusions      = ["information_schema/%", "pg_catalog/%", "pg_toast/%"]
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  depends_on = [aws_db_instance.warehouse]
}

# ===== SECURITY GROUP RULES: Glue <-> Data Warehouse =====
resource "aws_security_group_rule" "glue_to_warehouse_egress" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.glue_crawler.id
  source_security_group_id = aws_security_group.data_warehouse.id
}

resource "aws_security_group_rule" "warehouse_ingress_from_glue" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.data_warehouse.id
  source_security_group_id = aws_security_group.glue_crawler.id
}

# Self-referencing rule for Glue connections (required for Glue to work in VPC)
resource "aws_security_group_rule" "glue_self_ingress" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  security_group_id        = aws_security_group.glue_crawler.id
  source_security_group_id = aws_security_group.glue_crawler.id
}

