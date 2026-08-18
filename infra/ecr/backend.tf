terraform {
  backend "s3" {
    bucket       = "documind-ai-tfstate-847008502735"
    key          = "ecr/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}