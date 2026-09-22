resource "aws_bedrock_guardrail" "main" {
  name                      = "documind-ai-${var.environment}"
  description               = "Content and grounding safeguards for DocuMind RAG answers"
  blocked_input_messaging   = "This request was blocked by content policy"
  blocked_outputs_messaging = "This rrequest was blocked by content policy"

  content_policy_config {
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }

    filters_config {
      type            = "HATE"
      input_strength  = var.content_filter_strength
      output_strength = var.content_filter_strength
    }

    filters_config {
      type            = "INSULTS"
      input_strength  = var.content_filter_strength
      output_strength = var.content_filter_strength
    }

    filters_config {
      type            = "SEXUAL"
      input_strength  = var.content_filter_strength
      output_strength = var.content_filter_strength
    }

    filters_config {
      type            = "VIOLENCE"
      input_strength  = var.content_filter_strength
      output_strength = var.content_filter_strength
    }

    filters_config {
      type            = "MISCONDUCT"
      input_strength  = var.content_filter_strength
      output_strength = var.content_filter_strength
    }
  }

  contextual_grounding_policy_config {
    filters_config {
      type      = "GROUNDING"
      threshold = 0.7
    }

    filters_config {
      type      = "RELEVANCE"
      threshold = 0.7
    }
  }

  tags = {
    Project     = "documind-ai"
    Environment = var.environment
  }
}
