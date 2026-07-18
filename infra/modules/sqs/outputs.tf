output "queue_url" {
  value = aws_sqs_queue.ingestion.url
}

output "queue_arn" {
  value = aws_sqs_queue.ingestion.arn
}

output "dlq_arn" {
  value = aws_sqs_queue.ingestion_dlq.arn
}