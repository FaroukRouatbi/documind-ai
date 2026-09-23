output "redis_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  value = aws_elasticache_replication_group.redis.port
}

output "redis_auth_secret_arn" {
  value = aws_secretsmanager_secret.redis_auth.arn
}
