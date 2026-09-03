module "network" {
  source = "../../modules/network"

  vpc_cidr             = "10.0.0.0/16"
  environment          = "dev"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.101.0/24", "10.0.102.0/24"]
}

module "s3" {
  source = "../../modules/s3"

  environment = var.environment
}

module "iam" {
  source = "../../modules/iam"

  environment             = var.environment
  documents_bucket_arn    = module.s3.documents_bucket_arn
  db_secret_arn           = module.rds.db_secret_arn
  migration_db_secret_arn = module.rds.migration_db_secret_arn
  sqs_queue_arn           = module.sqs.ingestion_queue_arn
  aws_region              = var.aws_region
  documents_kms_key_arn   = module.s3.documents_kms_key_arn
}

module "rds" {
  source = "../../modules/rds"

  environment           = var.environment
  private_subnet_ids    = module.network.private_subnet_ids
  rds_security_group_id = module.network.rds_security_group_id
}

module "elasticache" {
  source = "../../modules/elasticache"

  environment             = "dev"
  private_subnet_ids      = module.network.private_subnet_ids
  redis_security_group_id = module.network.redis_security_group_id
}

module "cognito" {
  source = "../../modules/cognito"

  environment = var.environment
}

module "sqs" {
  source = "../../modules/sqs"

  environment = var.environment
}

module "ecs" {
  source = "../../modules/ecs"

  environment = var.environment

  # Networking (from the network module)
  vpc_id                = module.network.vpc_id
  public_subnet_ids     = module.network.public_subnet_ids
  alb_security_group_id = module.network.alb_security_group_id
  private_subnet_ids    = module.network.private_subnet_ids
  ecs_security_group_id = module.network.ecs_security_group_id

  # IAM roles (from the iam module)
  execution_role_arn   = module.iam.execution_role_arn
  api_task_role_arn    = module.iam.api_task_role_arn
  worker_task_role_arn = module.iam.worker_task_role_arn

  # Container images (from the ecr module)
  api_repository_url    = data.terraform_remote_state.ecr.outputs.api_repository_url
  worker_repository_url = data.terraform_remote_state.ecr.outputs.worker_repository_url

  # Runtime configuration for the containers
  documents_bucket_name       = module.s3.documents_bucket_name
  db_secret_arn               = module.rds.db_secret_arn
  migration_db_secret_arn     = module.rds.migration_db_secret_arn
  redis_endpoint              = module.elasticache.redis_endpoint
  sqs_queue_url               = module.sqs.queue_url
  cognito_user_pool_id        = module.cognito.user_pool_id
  cognito_user_pool_client_id = module.cognito.user_pool_client_id

  api_image_tag    = var.api_image_tag
  worker_image_tag = var.worker_image_tag
}

resource "aws_sqs_queue_policy" "ingestion_allow_s3" {
  queue_url = module.sqs.queue_url

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = module.sqs.ingestion_queue_arn
      Condition = {
        ArnEquals = { "aws:SourceArn" = module.s3.documents_bucket_arn }
      }
    }]
  })
}

resource "aws_s3_bucket_notification" "documents" {
  bucket = module.s3.documents_bucket_id

  queue {
    queue_arn = module.sqs.ingestion_queue_arn
    events    = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_sqs_queue_policy.ingestion_allow_s3]
}

data "terraform_remote_state" "ecr" {
  backend = "s3"
  config = {
    bucket = "documind-ai-tfstate-847008502735"
    key    = "ecr/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "local_file" "migration_network" {
  filename = "${path.module}/migration-network.json"
  content = jsonencode({
    awsvpcConfiguration = {
      subnets        = module.network.private_subnet_ids
      securityGroups = [module.network.ecs_security_group_id]
      assignPublicIp = "DISABLED"
    }
  })
}
