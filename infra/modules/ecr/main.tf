resource "aws_ecr_repository" "api" {
  name = "documind-ai-api-${var.environment}"

  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "worker" {
  name = "documind-ai-worker-${var.environment}"

  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}