# ===== ECS CLUSTER =====
resource "aws_ecs_cluster" "airflow" {
  name = "${var.project_name}-airflow-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled" # Save costs
  }

  tags = { Name = "${var.project_name}-airflow-cluster" }
}

resource "aws_ecs_cluster_capacity_providers" "airflow" {
  cluster_name = aws_ecs_cluster.airflow.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# ===== SECURITY GROUPS =====
resource "aws_security_group" "airflow" {
  name_prefix = "${var.project_name}-airflow-"
  description = "Security group for Airflow ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-airflow-sg" }
}

resource "aws_security_group" "database" {
  name_prefix = "${var.project_name}-db-"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.airflow.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-db-sg" }
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-alb-sg" }
}

# ===== RDS POSTGRES FOR AIRFLOW METADATA =====
resource "aws_db_subnet_group" "airflow" {
  name        = "${var.project_name}-airflow-db-subnet"
  description = "Subnet group for Airflow metadata database"

  subnet_ids = [
    aws_subnet.private_1.id,
    aws_subnet.private_2.id,
    aws_subnet.private_3.id,
  ]

  tags = { Name = "${var.project_name}-airflow-db-subnet" }
}

resource "aws_db_instance" "airflow" {
  identifier     = "${var.project_name}-airflow-db"
  instance_class = var.airflow_db_instance_class
  engine         = "postgres"
  engine_version = "17.4"

  username = "airflow"
  password = var.airflow_admin_password

  allocated_storage = var.airflow_db_allocated_storage
  db_name           = "airflow"

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.airflow.name
  publicly_accessible    = false

  skip_final_snapshot = true # For dev/learning - skip snapshot on destroy

  tags = { Name = "${var.project_name}-airflow-db" }
}

