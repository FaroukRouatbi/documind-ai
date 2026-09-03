resource "aws_elasticache_subnet_group" "redis" {
  name       = "documind-ai-cache-subnet-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "documind-ai-redis-${var.environment}"
  description                = "Redis cache for DocuMind AI (${var.environment})"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = "cache.t4g.micro"
  num_cache_clusters         = 1
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [var.redis_security_group_id]
  at_rest_encryption_enabled = true

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}
