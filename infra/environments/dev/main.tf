terraform {
  backend "s3" {
    bucket = "documind-ai-tfstate-847008502735"
    key = "dev/network.tfstate"
    region = "us-east-1"
    encrypt = true
    use_lockfile = true
  }
}

provider "aws" {
    region = "us-east-1"
}

module "network" {
  source = "../../modules/network"

  vpc_cidr             = "10.0.0.0/16"
  environment          = "dev"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.101.0/24", "10.0.102.0/24"]
}

module "s3" {
  source = "../../modules/s3"

  environment = "dev"
}

module "iam" {
  source = "../../modules/iam"

  environment = "dev"
  documents_bucket_arn = module.s3.documents_bucket_arn
  db_secret_arn        = module.rds.db_secret_arn
  sqs_queue_arn = module.sqs.queue_arn
}

module "rds" {
  source = "../../modules/rds"

  environment = "dev"
  private_subnet_ids = module.network.private_subnet_ids
  rds_security_group_id = module.network.rds_security_group_id
}

module "elasticache" {
  source = "../../modules/elasticache"

  environment = "dev"
  private_subnet_ids = module.network.private_subnet_ids
  redis_security_group_id = module.network.rds_security_group_id
}

module "cognito" {
  source = "../../modules/cognito"

  environment = "dev"
}

module "sqs" {
  source = "../../modules/sqs"

  environment = "dev"
}

module "ecr" {
  source = "../../modules/ecr"

  environment = "dev"
}

