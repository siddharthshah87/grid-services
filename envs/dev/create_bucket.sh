
# Ensure required environment variables are set
: "${AWS_PROFILE?Must set AWS_PROFILE to your AWS profile name}"
: "${BUCKET?Must set BUCKET to the S3 bucket name for Terraform state}"
REGION="${AWS_REGION:-us-west-2}"

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

