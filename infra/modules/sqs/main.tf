resource "aws_sqs_queue" "ingestion_dlq" {
  name                    = "documind-ai-ingestion-dlq-${var.environment}"
  sqs_managed_sse_enabled = true

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "ingestion" {
  name                    = "documind-ai-ingestion-${var.environment}"
  sqs_managed_sse_enabled = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}
