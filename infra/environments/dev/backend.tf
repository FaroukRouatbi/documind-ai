terraform {
  backend "s3" {
    bucket       = "documind-ai-tfstate-847008502735"
    key          = "dev/network.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}