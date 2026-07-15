output "vpc_id" {
  value = module.network.vpc_id
}

output "ecs_security_group_id" {
  value = module.network.ecs_security_group_id
}

output "documents_bucket_name" {
  value = module.s3.documents_bucket_name
}

output "documents_bucket_arn" {
  value = module.s3.documents_bucket_arn
}

output "db_endpoint" {
  value = module.rds.db_endpoint
}

output "db_secret_arn" {
  value = module.rds.db_secret_arn
}

output "redis_endpoint" {
  value = module.elasticache.redis_endpoint
}

output "cognito_user_pool_id" {
  value = module.cognito.user_pool_id
}

output "cognito_user_pool_client_id" {
  value = module.cognito.user_pool_client_id
}

output "api_repository_url" {
  value = module.ecr.api_repository_url
}

output "worker_repository_url" {
  value = module.ecr.worker_repository_url
}