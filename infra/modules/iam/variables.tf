variable "environment" {
  type = string
}

variable "documents_bucket_arn" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "migration_db_secret_arn" {
  type = string
}

variable "sqs_queue_arn" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "documents_kms_key_arn" {
  type = string
}

variable "bedrock_guardrail_arn" {
  description = "ARN of the Bedrock guardrail applied to generation calls"
  type        = string
}

variable "claude_inference_profile_id" {
  description = "Bedrock inference profile ID used for answer generation"
  type        = string
  default     = "global.anthropic.claude-sonnet-4-6"
}

variable "claude_model_id" {
  description = "Underlying foundation model ID behind the Claude inference profile"
  type        = string
}

variable "redis_auth_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the Redis AUTH token"
  type        = string
}
