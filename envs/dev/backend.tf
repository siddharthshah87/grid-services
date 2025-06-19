terraform {
  backend "s3" {
    bucket         = "tf-state-grid-services"
    key            = "dev/terraform.tfstate"
    region         = "us-west-1"
    dynamodb_table = "tf-lock-grid-services"
    encrypt        = true
  }
}

