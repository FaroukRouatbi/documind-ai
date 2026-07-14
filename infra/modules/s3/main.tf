# --- KMS key for documents bucket encryption ---

resource "aws_kms_key" "documents" {
  description             = "Encrypts DocuMind AI documents"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Project = "documind-ai"
  }
}

# --- S3 bucket for documents ---

data "aws_caller_identity" "current" {}


resource "aws_s3_bucket" "documents" {
  bucket = "documind-ai-documents-${data.aws_caller_identity.current.account_id}-${var.environment}"

  tags = {
    Project = "documind-ai"
    Purpose = "documents"
  }

  # Deliberately no prevent_destroy in dev — see note below.
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.documents.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "intelligent-tiering-current-objects"
    status = "Enabled"

    transition {
      days          = 0
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}