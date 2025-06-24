# Use the profile that holds your SSO creds
export AWS_PROFILE=AdministratorAccess-923675928909
export BUCKET=tf-state-grid-services-923675928909   # or your chosen name
export REGION=us-west-1

aws s3api create-bucket \
  --bucket "$BUCKET" \
  --create-bucket-configuration LocationConstraint="$REGION"

# (strongly recommended) turn on versioning
aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled

# (optional) block all public access
aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

