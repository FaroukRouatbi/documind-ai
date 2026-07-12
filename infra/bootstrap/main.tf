terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92"
    }
  }

  required_version = ">= 1.2"
}

provider "aws" {
  region = "us-east-1" 
}

data "aws_caller_identity" "current" {}

# --- KMS key for state bucket encryption ---

resource "aws_kms_key" "tfstate" {
  description             = "Encrypts DocuMind AI Terraform state bucket objects"
  deletion_window_in_days = 10
  enable_key_rotation      = true

  tags = {
    Project = "documind-ai"
  }
}

# --- S3 bucket for remote state ---

resource "aws_s3_bucket" "tfstate" {
  bucket = "documind-ai-tfstate-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project = "documind-ai"
    Purpose = "terraform-state"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.tfstate.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

