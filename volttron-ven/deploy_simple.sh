#!/bin/bash
# Deploy simplified VEN to ECS

set -e

CLUSTER="hems-ecs-cluster"
SERVICE="volttron-ven"
ECR_REPO="923675928909.dkr.ecr.us-west-2.amazonaws.com/volttron-ven"
IMAGE_TAG="simple-latest"

echo "========== DEPLOYING SIMPLIFIED VEN =========="
echo "Image: $ECR_REPO:$IMAGE_TAG"
echo ""

# Get current task definition
CURRENT_TASK_DEF=$(aws ecs describe-services \
    --cluster $CLUSTER \
    --services $SERVICE \
    --query 'services[0].taskDefinition' \
    --output text)

echo "Current task definition: $CURRENT_TASK_DEF"

# Get the task definition JSON
TASK_DEF_JSON=$(aws ecs describe-task-definition --task-definition $CURRENT_TASK_DEF)

# Update the image in the container definition
NEW_TASK_DEF=$(echo $TASK_DEF_JSON | jq --arg IMAGE "$ECR_REPO:$IMAGE_TAG" '
    .taskDefinition |
    .containerDefinitions[0].image = $IMAGE |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
')

# Register new task definition
echo ""
echo "Registering new task definition with simplified VEN..."
NEW_TASK_ARN=$(echo $NEW_TASK_DEF | jq -c '.' | \
    aws ecs register-task-definition --cli-input-json file:///dev/stdin --query 'taskDefinition.taskDefinitionArn' --output text)

echo "New task definition: $NEW_TASK_ARN"

# Update service
echo ""
echo "Updating service to use new task definition..."
aws ecs update-service \
    --cluster $CLUSTER \
    --service $SERVICE \
    --task-definition $NEW_TASK_ARN \
    --force-new-deployment \
    --no-cli-pager \
    --query 'service.{serviceName:serviceName, taskDefinition:taskDefinition, desiredCount:desiredCount}' \
    --output table

echo ""
echo "✅ Deployment initiated. Monitor with:"
echo "   aws ecs describe-services --cluster $CLUSTER --services $SERVICE"
echo "   aws logs tail /ecs/volttron-ven --follow"
