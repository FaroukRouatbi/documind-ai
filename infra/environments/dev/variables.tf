variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "api_image_tag" {
  type    = string
  default = "v11"
}

variable "worker_image_tag" {
  type    = string
  default = "v10"
}