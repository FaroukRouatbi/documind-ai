resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*-_=+"
}

resource "aws_db_subnet_group" "db" {
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.environment}-db-subnet-group"
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_db_parameter_group" "db" {
  name   = "${var.environment}-postgres17"
  family = "postgres17"

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_db_instance" "db" {
  engine         = "postgres"
  engine_version = "17"
  instance_class = "db.t4g.micro"

  allocated_storage = 20
  db_name           = "documind"
  username          = var.db_username
  password          = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.db.name
  parameter_group_name   = aws_db_parameter_group.db.name
  vpc_security_group_ids = [var.rds_security_group_id]

  publicly_accessible = false
  skip_final_snapshot  = true

  tags = {
    Name        = "${var.environment}-documind-db"
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.environment}/documind-ai/db-credentials"
  description = "PostgreSQL credentials for the RAG application running on ECS Fargate (${var.environment} environment)"
  recovery_window_in_days = 0

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    host     = aws_db_instance.db.address
    port     = aws_db_instance.db.port
    dbname   = aws_db_instance.db.db_name
  })
}