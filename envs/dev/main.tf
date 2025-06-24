module "vpc" {
  source     = "../../modules/vpc"
  name       = "hems-demo-vpc"
  cidr_block = "10.10.0.0/16"
  az_count   = 2
  tags = {
    Project = "hems-demo"
    Env     = "dev"
 }
}
module "ecr_openleadr" {
  source = "../../modules/ecr-repo"
  name   = "openleadr-vtn"
  tags = {
    Project = "grid-services"
    Component = "OpenADR"
  }
}

module "ecr_volttron" {
  source = "../../modules/ecr-repo"
  name   = "volttron-ven"
  tags = {
    Project = "grid-services"
    Component = "VOLTTRON"
  }
}
