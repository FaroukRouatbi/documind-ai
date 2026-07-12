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