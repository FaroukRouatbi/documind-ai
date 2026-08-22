# --- Trust policy: allows ECS to assume both roles below ---

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# --- ECS task execution role (used by the ECS agent: pull images, log, inject secrets) ---

resource "aws_iam_role" "ecs_execution" {
  name               = "documind-ai-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}


# --- ECS task execution role (used by the ECS agent: to access secrets) ---

data "aws_iam_policy_document" "execution_secrets_permissions" {
  statement {
    sid = "SecretsAccess"

    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [
      var.db_secret_arn,
      var.migration_db_secret_arn
    ]
  }
}

resource "aws_iam_policy" "execution_secrets_policy" {
  name   = "documind-ai-ecs-secrets-permissions"
  policy = data.aws_iam_policy_document.execution_secrets_permissions.json
}

resource "aws_iam_role_policy_attachment" "execution_secrets_attach" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = aws_iam_policy.execution_secrets_policy.arn
}

# --- API task role ---
resource "aws_iam_role" "ecs_task_api" {
  name = "documind-ai-ecs-task-api-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

data "aws_iam_policy_document" "api_task_permissions" {
  statement {
    sid = "DocumentBucketPut"
    actions = [ "s3:PutObject" ]
    resources = [ "${var.documents_bucket_arn}/*" ]
  }

  statement {
    sid = "DocumentKMSEncrypt"
    actions = [ "kms:GenerateDataKey" ]
    resources = [ var.documents_kms_key_arn ]
  }

  statement {
    sid = "SecretsAccess"
    actions = [ "secretsmanager:GetSecretValue" ]
    resources = [ var.db_secret_arn ]
  }
}

resource "aws_iam_policy" "api_task_policy" {
  name = "documind-ai-ecs-task-api-permissions-${var.environment}"
  policy = data.aws_iam_policy_document.api_task_permissions.json
}

resource "aws_iam_role_policy_attachment" "api_task_attach" {
  role       = aws_iam_role.ecs_task_api.name
  policy_arn = aws_iam_policy.api_task_policy.arn
}

# --- Worker task role ---
resource "aws_iam_role" "ecs_task_worker" {
  name               = "documind-ai-ecs-task-worker-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

data "aws_iam_policy_document" "worker_task_permissions" {
  statement {
    sid = "DocumentBucketGet"
    actions = [ "s3:GetObject" ]
    resources = [ "${var.documents_bucket_arn}/*" ]
  }

  statement {
    sid = "DocumentsKMSDecrypt"
    actions = [ "kms:Decrypt" ]
    resources = [ var.documents_kms_key_arn ]
  }

  statement {
    sid = "BedRockAccess"
    actions = [ 
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
     ]
     resources = [ 
      "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0",
      ]
  }

  statement {
    sid = "SQSConsume"
    actions = [ 
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
     ]
     resources = [ var.sqs_queue_arn ]
  }

  statement {
    sid = "SecretsAccess"
    actions = [ "secretsmanager:GetSecretValue" ]
    resources = [ var.db_secret_arn ]
  }
}

resource "aws_iam_policy" "worker_task_policy" {
  name   = "documind-ai-ecs-task-worker-permissions-${var.environment}"
  policy = data.aws_iam_policy_document.worker_task_permissions.json
}

resource "aws_iam_role_policy_attachment" "worker_task_attach" {
  role = aws_iam_role.ecs_task_worker.name
  policy_arn = aws_iam_policy.worker_task_policy.arn
}