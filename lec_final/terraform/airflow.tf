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



# ===== EFS FOR AIRFLOW DAGS =====
resource "aws_security_group" "efs" {
  name_prefix = "${var.project_name}-efs-"
  description = "Security group for EFS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.airflow.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-efs-sg" }
}

resource "aws_efs_file_system" "airflow_dags" {
  tags = { Name = "${var.project_name}-airflow-dags" }
}

resource "aws_efs_mount_target" "dags_1" {
  file_system_id  = aws_efs_file_system.airflow_dags.id
  subnet_id       = aws_subnet.private_1.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "dags_2" {
  file_system_id  = aws_efs_file_system.airflow_dags.id
  subnet_id       = aws_subnet.private_2.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "dags_3" {
  file_system_id  = aws_efs_file_system.airflow_dags.id
  subnet_id       = aws_subnet.private_3.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_file_system" "airflow_config" {
  tags = { Name = "${var.project_name}-airflow-config" }
}

resource "aws_efs_mount_target" "config_1" {
  file_system_id  = aws_efs_file_system.airflow_config.id
  subnet_id       = aws_subnet.private_1.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "config_2" {
  file_system_id  = aws_efs_file_system.airflow_config.id
  subnet_id       = aws_subnet.private_2.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "config_3" {
  file_system_id  = aws_efs_file_system.airflow_config.id
  subnet_id       = aws_subnet.private_3.id
  security_groups = [aws_security_group.efs.id]
}

# ===== CLOUDWATCH LOG GROUPS =====
resource "aws_cloudwatch_log_group" "airflow" {
  name              = "/aws/ecs/${var.project_name}-airflow"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "dag_sync" {
  name              = "/aws/ecs/${var.project_name}-dag-sync"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "s3" {
  name              = "/aws/s3/${var.project_name}"
  retention_in_days = var.log_retention_days
}

# ===== AIRFLOW WEBSERVER TASK DEFINITION =====
resource "aws_ecs_task_definition" "webserver" {
  family                   = "${var.project_name}-airflow-webserver"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.airflow_cpu
  memory                   = var.airflow_memory
  execution_role_arn       = aws_iam_role.airflow_execution.arn
  task_role_arn            = aws_iam_role.airflow_task.arn

  container_definitions = jsonencode([{
    name      = "airflow-webserver"
    image     = var.airflow_image
    essential = true

    portMappings = [{
      containerPort = 8080
      protocol      = "tcp"
    }]

    environment = [
      { name = "AIRFLOW__CORE__EXECUTOR", value = "LocalExecutor" },
      { name = "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", value = "postgresql://airflow:${var.airflow_admin_password}@${aws_db_instance.airflow.endpoint}/airflow" },
      { name = "AIRFLOW__CORE__FERNET_KEY", value = var.airflow_fernet_key },
      { name = "AIRFLOW__WEBSERVER__SECRET_KEY", value = var.airflow_webserver_secret_key },
      { name = "AIRFLOW__CORE__DAGS_FOLDER", value = "/opt/airflow/dags" },
      { name = "AIRFLOW__CORE__LOAD_EXAMPLES", value = "True" },
      { name = "_AIRFLOW_WWW_USER_USERNAME", value = var.airflow_admin_username },
      { name = "_AIRFLOW_WWW_USER_PASSWORD", value = var.airflow_admin_password },
      { name = "S3_CONFIG_BUCKET", value = aws_s3_bucket.airflow.id },
    ]

    mountPoints = [
      { sourceVolume = "airflow-dags", containerPath = "/opt/airflow/dags" },
      { sourceVolume = "airflow-config", containerPath = "/opt/airflow/config" },
    ]

    command = ["bash", "-c", <<-EOT
      echo "Installing AWS provider for Airflow..."
      pip install --no-cache-dir apache-airflow-providers-amazon==8.16.0
      echo "Starting Airflow Webserver..."
      if aws s3 ls s3://$S3_CONFIG_BUCKET/config/airflow.cfg; then
        echo "Found custom airflow.cfg in S3, downloading..."
        aws s3 cp s3://$S3_CONFIG_BUCKET/config/airflow.cfg /opt/airflow/config/airflow.cfg
        export AIRFLOW_CONFIG=/opt/airflow/config/airflow.cfg
      fi
      if aws s3 ls s3://$S3_CONFIG_BUCKET/config/webserver_config.py; then
        aws s3 cp s3://$S3_CONFIG_BUCKET/config/webserver_config.py /opt/airflow/config/webserver_config.py
        export AIRFLOW__WEBSERVER__CONFIG_FILE=/opt/airflow/config/webserver_config.py
      fi
      airflow db init
      airflow db check
      airflow users list | grep -q $${_AIRFLOW_WWW_USER_USERNAME} || \
      airflow users create \
        --username $${_AIRFLOW_WWW_USER_USERNAME} \
        --firstname Admin --lastname User --role Admin \
        --email admin@example.com \
        --password $${_AIRFLOW_WWW_USER_PASSWORD}
      airflow webserver
    EOT
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.airflow.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "webserver"
      }
    }
  }])

  volume {
    name = "airflow-dags"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.airflow_dags.id
    }
  }

  volume {
    name = "airflow-config"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.airflow_config.id
    }
  }

  tags = { Name = "${var.project_name}-airflow-webserver" }
}

# ===== AIRFLOW SCHEDULER TASK DEFINITION =====
resource "aws_ecs_task_definition" "scheduler" {
  family                   = "${var.project_name}-airflow-scheduler"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.airflow_cpu
  memory                   = var.airflow_memory
  execution_role_arn       = aws_iam_role.airflow_execution.arn
  task_role_arn            = aws_iam_role.airflow_task.arn

  container_definitions = jsonencode([{
    name      = "airflow-scheduler"
    image     = var.airflow_image
    essential = true

    environment = [
      { name = "AIRFLOW__CORE__EXECUTOR", value = "LocalExecutor" },
      { name = "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", value = "postgresql://airflow:${var.airflow_admin_password}@${aws_db_instance.airflow.endpoint}/airflow" },
      { name = "AIRFLOW__CORE__FERNET_KEY", value = var.airflow_fernet_key },
      { name = "AIRFLOW__CORE__DAGS_FOLDER", value = "/opt/airflow/dags" },
      { name = "AIRFLOW__CORE__LOAD_EXAMPLES", value = "False" },
      { name = "S3_CONFIG_BUCKET", value = aws_s3_bucket.airflow.id },
    ]

    mountPoints = [
      { sourceVolume = "airflow-dags", containerPath = "/opt/airflow/dags" },
      { sourceVolume = "airflow-config", containerPath = "/opt/airflow/config" },
    ]

    command = ["bash", "-c", <<-EOT
      echo "Installing AWS provider for Airflow..."
      pip install --no-cache-dir apache-airflow-providers-amazon==8.16.0
      echo "Starting Airflow Scheduler..."
      if aws s3 ls s3://$S3_CONFIG_BUCKET/config/airflow.cfg; then
        aws s3 cp s3://$S3_CONFIG_BUCKET/config/airflow.cfg /opt/airflow/config/airflow.cfg
        export AIRFLOW_CONFIG=/opt/airflow/config/airflow.cfg
      fi
      airflow scheduler
    EOT
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.airflow.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "scheduler"
      }
    }
  }])

  volume {
    name = "airflow-dags"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.airflow_dags.id
    }
  }

  volume {
    name = "airflow-config"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.airflow_config.id
    }
  }

  tags = { Name = "${var.project_name}-airflow-scheduler" }
}

# ===== DAG SYNC TASK DEFINITION =====
resource "aws_ecs_task_definition" "dag_sync" {
  family                   = "${var.project_name}-dag-sync"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.airflow_execution.arn
  task_role_arn            = aws_iam_role.dag_sync_task.arn

  container_definitions = jsonencode([{
    name      = "dag-sync"
    image     = "amazon/aws-cli:latest"
    essential = true

    environment = [
      { name = "S3_BUCKET", value = aws_s3_bucket.airflow.id },
      { name = "S3_PREFIX", value = "dags/" },
      { name = "EFS_MOUNT_PATH", value = "/opt/airflow/dags" },
    ]

    mountPoints = [
      { sourceVolume = "airflow-dags", containerPath = "/opt/airflow/dags" },
    ]

    entryPoint = ["/bin/sh", "-c"]

    command = [<<-EOT
      echo "Starting DAG sync from S3 to EFS..."
      mkdir -p $EFS_MOUNT_PATH
      aws s3 sync s3://$S3_BUCKET/$S3_PREFIX $EFS_MOUNT_PATH --delete --exact-timestamps
      echo "DAG sync completed successfully"
      ls -la $EFS_MOUNT_PATH
    EOT
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.dag_sync.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "dag-sync"
      }
    }
  }])

  volume {
    name = "airflow-dags"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.airflow_dags.id
    }
  }

  volume {
    name = "airflow-config"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.airflow_config.id
    }
  }

  tags = { Name = "${var.project_name}-dag-sync" }
}

# ===== APPLICATION LOAD BALANCER =====
resource "aws_lb" "airflow" {
  name               = "${var.project_name}-airflow-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]
  security_groups    = [aws_security_group.alb.id]

  tags = { Name = "${var.project_name}-airflow-alb" }
}

resource "aws_lb_target_group" "airflow" {
  name        = "${var.project_name}-airflow-tg"
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path     = "/health"
    protocol = "HTTP"
  }

  tags = { Name = "${var.project_name}-airflow-tg" }
}

resource "aws_lb_listener" "airflow" {
  load_balancer_arn = aws_lb.airflow.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.airflow.arn
  }
}

# ===== ECS SERVICES =====
resource "aws_ecs_service" "webserver" {
  name            = "${var.project_name}-airflow-webserver"
  cluster         = aws_ecs_cluster.airflow.id
  task_definition = aws_ecs_task_definition.webserver.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.airflow.id]
    subnets          = [aws_subnet.public_1.id, aws_subnet.public_2.id]
  }

  load_balancer {
    container_name   = "airflow-webserver"
    container_port   = 8080
    target_group_arn = aws_lb_target_group.airflow.arn
  }

  depends_on = [aws_db_instance.airflow, aws_lb_listener.airflow]

  tags = { Name = "${var.project_name}-airflow-webserver" }
}

resource "aws_ecs_service" "scheduler" {
  name            = "${var.project_name}-airflow-scheduler"
  cluster         = aws_ecs_cluster.airflow.id
  task_definition = aws_ecs_task_definition.scheduler.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.airflow.id]
    subnets          = [aws_subnet.public_1.id, aws_subnet.public_2.id]
  }

  depends_on = [aws_db_instance.airflow]

  tags = { Name = "${var.project_name}-airflow-scheduler" }
}

# ===== EVENTBRIDGE RULE FOR SCHEDULED DAG SYNC =====
resource "aws_cloudwatch_event_rule" "dag_sync" {
  name                = "${var.project_name}-dag-sync-schedule"
  description         = "Trigger DAG sync every 5 minutes"
  schedule_expression = "rate(5 minutes)"
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "dag_sync" {
  rule     = aws_cloudwatch_event_rule.dag_sync.name
  arn      = aws_ecs_cluster.airflow.arn
  role_arn = aws_iam_role.eventbridge_execution.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.dag_sync.arn
    launch_type         = "FARGATE"

    network_configuration {
      assign_public_ip = true
      security_groups  = [aws_security_group.airflow.id]
      subnets          = [aws_subnet.public_1.id, aws_subnet.public_2.id]
    }
  }
}