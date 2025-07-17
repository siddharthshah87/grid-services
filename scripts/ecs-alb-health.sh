#!/usr/bin/env bash
set -Eeuo pipefail

# -------------- CONFIG  -------------------------------------------------
CLUSTERS=("hems-ecs-cluster")        # add more clusters if needed
HEALTH_PATH="/health"               # path to curl on the ALB
LOG_LINES=40                        # how many log lines to show when failing
PROFILE="AdministratorAccess-923675928909"  # AWS profile
REGION=$(aws configure get region --profile "$PROFILE")
DATE_STR=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "─── ECS and ALB Health check ───"

# -------------- FUNCTIONS  ----------------------------------------------

json() { jq -r "$@" ; }

check_service() {
  echo "─── ECS and ALB Health check Service ───"
  local cluster="$1" service="$2"

  # --- Basic service status --------------------------------------------
  local svc_json
  svc_json=$(aws ecs describe-services --cluster "$cluster" \
               --services "$service" --profile "$PROFILE" --output json)

  local desired running pending taskDef
  desired=$(echo "$svc_json" | json '.services[0].desiredCount')
  running=$(echo "$svc_json" | json '.services[0].runningCount')
  pending=$(echo "$svc_json" | json '.services[0].pendingCount')
  taskDef=$(echo "$svc_json" | json '.services[0].taskDefinition')

  # --- Load balancer details -------------------------------------------
  local tg_arn alb_arn
  local alb_dns=""                       #— give it a default

  tg_arn=$(echo "$svc_json" | json '.services[0].loadBalancers[0].targetGroupArn // empty')

  if [[ -n "$tg_arn" ]]; then
    alb_arn=$(aws elbv2 describe-target-groups --target-group-arns "$tg_arn" \
              --query 'TargetGroups[0].LoadBalancerArns[0]' --output text \
              --profile "$PROFILE" 2>/dev/null | tr -d '\r')

    if [[ -n "$alb_arn" && "$alb_arn" != "None" ]]; then
      alb_dns=$(aws elbv2 describe-load-balancers --load-balancer-arns "$alb_arn" \
                --query 'LoadBalancers[0].DNSName' --output text \
                --profile "$PROFILE" 2>/dev/null | tr -d '\r')
    fi
  fi

  # --- Target health ----------------------------------------------------
  local target_state
  if [[ -n "$tg_arn" ]]; then
    target_state=$(aws elbv2 describe-target-health \
                     --target-group-arn "$tg_arn" \
                     --query 'TargetHealthDescriptions[*].TargetHealth.State' \
                     --output text --profile "$PROFILE" 2>/dev/null | sort -u | tr '\n' ',' | sed 's/,$//')
  else
    target_state="no-target-group"
  fi

  # --- ALB curl check ---------------------------------------------------
  local http_code curl_msg
  if [[ -n "$alb_dns" ]]; then
    http_code=$(curl -s -o /dev/null -w '%{http_code}' "http://$alb_dns${HEALTH_PATH}")
    curl_msg="HTTP $http_code"
  else
    curl_msg="no-alb"
  fi

  # --- Decide OK / FAIL -------------------------------------------------
  local status="OK"
  [[ "$desired" -ne "$running" || "$target_state" != "healthy"* || "$curl_msg" != "HTTP 200" ]] && status="FAIL"

  printf "%-25s %-8s desired=%s running=%s tgt=%s curl=%s\n" \
         "$service" "$status" "$desired" "$running" "$target_state" "$curl_msg"

  # --- Fetch logs if failing -------------------------------------------
  if [[ "$status" == "FAIL" ]]; then
    echo "─── Logs (last $LOG_LINES lines) ───"
    local log_group
    log_group=$(aws ecs describe-task-definition --task-definition "$taskDef" \
                 --profile "$PROFILE" \
                 --query 'taskDefinition.containerDefinitions[0].logConfiguration.options."awslogs-group"' \
                 --output text)
    aws logs tail "$log_group" --since 10m --profile "$PROFILE"
    echo
  fi
}


# -------------- MAIN  ---------------------------------------------------
echo "▶︎ Health run $DATE_STR ($REGION, profile=$PROFILE)"
echo

for cluster in "${CLUSTERS[@]}"; do
  echo "=== Cluster: $cluster ==="
  svc_list=$(aws ecs list-services --cluster "$cluster" --profile "$PROFILE" --query 'serviceArns[*]' --output text)
  for svc_arn in $svc_list; do
    svc_name=$(basename "$svc_arn")
    check_service "$cluster" "$svc_name"
  done
  echo
done
