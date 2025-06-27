terraform {
  backend "s3" {
    bucket         = "tf-state-grid-services-923675928909"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    use_lockfile   = true
    encrypt        = true
  }
}

