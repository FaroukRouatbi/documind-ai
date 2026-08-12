resource "aws_sqs_queue" "ingestion_dlq" {
  name = "documind-ai-ingestion-dlq-${var.environment}"

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "ingestion" {
  name = "documind-ai-ingestion-${var.environment}"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_sqs_queue_policy" "ingestion_allow_s3" {
  queue_url = aws_sqs_queue.ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action = "sqs:SendMessage"
      Resource = aws_sqs_queue.ingestion.arn
      Condition = {
        ArnEquals = { "aws:SourceArn" = var.documents_bucket_arn }
      }
    }]
  })
}