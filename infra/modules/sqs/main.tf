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