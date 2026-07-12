terraform {
  backend "s3" {
    bucket = "documind-ai-tfstate-847008502735"
    key = "dev/network.tfstate"
    region = "us-east-1"
    encrypt = true
    use_lockfile = true
  }
}

provider "aws" {
    region = "us-east-1"
}

module "network" {
  source = "../../modules/network"

  vpc_cidr             = "10.0.0.0/16"
  environment          = "dev"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.101.0/24", "10.0.102.0/24"]
}

module "s3" {
  source = "../../modules/s3"

  environment = "dev"
}