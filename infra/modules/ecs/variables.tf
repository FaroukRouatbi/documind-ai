variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "execution_role_arn" {
  type = string
}

variable "task_role_arn" {
  type = string
}

variable "api_repository_url" {
  type = string
}

variable "worker_repository_url" {
  type = string
}

variable "documents_bucket_name" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "redis_endpoint" {
  type = string
}

variable "sqs_queue_url" {
  type = string
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_user_pool_client_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "ecs_security_group_id" {
  type = string
}