variable "environment" {
  description = "Deployment environment (dev/prod)"
  type        = string
}

variable "content_filter_strength" {
  description = "Strength for hate/insults/sexual/violence/misconduct filters"
  type        = string
  default     = "MEDIUM"
}
