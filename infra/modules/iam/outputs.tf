output "execution_role_arn" {
  value = aws_iam_role.ecs_execution.arn
}

output "api_task_role_arn" {
  value = aws_iam_role.ecs_task_api.arn
}

output "worker_task_role_arn" {
  value = aws_iam_role.ecs_task_worker.arn
}
