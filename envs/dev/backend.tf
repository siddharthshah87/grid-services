terraform {
  backend "s3" {
    bucket         = "tf-state-grid-services-923675928909-v2"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "tf-lock-923675928909"
  }
}

