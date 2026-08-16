variable "environment" {
  type = string
}

variable "documents_bucket_arn" {
  type = string
}

variable "db_secret_arn" {
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