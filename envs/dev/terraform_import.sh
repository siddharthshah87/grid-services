#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE=AdministratorAccess-923675928909
#ECR repo
terraform import module.ecr_openleadr.aws_ecr_repository.this openleadr-vtn
terraform import module.ecr_volttron.aws_ecr_repository.this volttron-ven
#IAM roles
terraform import module.ecs_task_roles.aws_iam_role.execution grid-sim-task-execution
terraform import module.ecs_task_roles.aws_iam_role.iot_mqtt grid-sim-task-iot
#IOT policies
terraform import module.iot_core.aws_iot_policy.allow_publish_subscribe volttron_policy
#ALB and Target group
aws elbv2 describe-load-balancers --names openadr-vtn-alb --region us-west-2
aws elbv2 describe-target-groups --names openadr-vtn-alb-tg --region us-west-2
terraform import module.openadr_alb.aws_lb.this arn:aws:elasticloadbalancing:us-west-2:923675928909:loadbalancer/app/openadr-vtn-alb/57c4e45e0573e5dc
terraform import module.openadr_alb.aws_lb_target_group.this arn:aws:elasticloadbalancing:us-west-2:923675928909:targetgroup/openadr-vtn-alb-tg/26baffc1c075e1a6

