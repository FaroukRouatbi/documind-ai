resource "aws_elasticache_subnet_group" "redis" {
  name       = "documind-ai-cache-subnet-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "documind-ai-redis-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [var.redis_security_group_id]

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}