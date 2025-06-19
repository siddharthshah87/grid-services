terraform {
  backend "s3" {
    bucket         = "tf-state-${data.aws_caller_identity.current.account_id}"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "tf-lock-${data.aws_caller_identity.current.account_id}"
    encrypt        = true
  }
}

