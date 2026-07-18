output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "aws_ecs_task_definition_api_arn" {
  value = aws_ecs_task_definition.api.arn
}

output "aws_cloudwatch_log_group_api_arn" {
  value = aws_cloudwatch_log_group.api.arn
}

output "aws_ecs_task_definition_worker_arn" {
  value = aws_ecs_task_definition.worker.arn
}

output "aws_cloudwatch_log_group_worker_arn" {
  value = aws_cloudwatch_log_group.worker.arn
}