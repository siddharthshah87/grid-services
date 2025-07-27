#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# ECS + ALB one‑shot health snapshot
#   • Prints desired/running counts, target‑group health, last logs per service
#   • Never hangs: every AWS CLI call is wrapped in timeout & short CLI time‑outs
#   • Works with either static or dynamic port mappings (uses target‑group API)
#   • Requires: bash 4+, coreutils (timeout), jq, AWS CLI v2
# -----------------------------------------------------------------------------
set -Eeuo pipefail

# ─── Config (override via env vars or CLI args) ───────────────────────────────
REGION="${AWS_REGION:-us-west-2}"
PROFILE="${AWS_PROFILE:-default}"
CLUSTER="${1:-hems-ecs-cluster}"
LOG_LINES="${LOG_LINES:-40}"
TIMEOUT="${TIMEOUT:-20s}"        # timeout per AWS call

# ─── AWS CLI base flags ———————————————————————————————————————————————
AWS_BASE=(aws --region "$REGION" --profile "$PROFILE" \
              --cli-connect-timeout 5 --cli-read-timeout 30 --no-paginate)

# helper: AWS call with global timeout
timeout_cmd() { timeout -k 5 "$TIMEOUT" "${AWS_BASE[@]}" "$@"; }

# ANSI colors
GREEN=$(tput setaf 2); RED=$(tput setaf 1); YEL=$(tput setaf 3); RESET=$(tput sgr0)

# ─── Per‑service check ————————————————————————————————————————————————
check_service() {
  local svc_arn="$1" svc_name="${svc_arn##*/}"

  # describe the service
  local svc_json
  if ! svc_json=$(timeout_cmd ecs describe-services --cluster "$CLUSTER" \
                    --services "$svc_arn" --output json 2>/dev/null); then
    echo -e "${RED}$svc_name    ✖ describe-services failed${RESET}"
    return
  fi

  local desired running tg_arn
  desired=$(jq -r '.services[0].desiredCount // 0' <<<"$svc_json")
  running=$(jq -r '.services[0].runningCount // 0' <<<"$svc_json")
  tg_arn=$(jq -r '.services[0].loadBalancers[0].targetGroupArn // empty' <<<"$svc_json")

  # default summary line
  local summary="$svc_name    desired=$desired running=$running"

  # if a target group is attached, fetch its first target health
  if [[ -n "$tg_arn" ]]; then
    local th_json state reason
    if th_json=$(timeout_cmd elbv2 describe-target-health --target-group-arn "$tg_arn" --output json 2>/dev/null); then
      state=$(jq -r '.TargetHealthDescriptions[0].TargetHealth.State' <<<"$th_json")
      reason=$(jq -r '.TargetHealthDescriptions[0].TargetHealth.Reason // ""' <<<"$th_json")
      summary+="  tg=$state $reason"
    else
      summary+="  tg=unknown"
    fi
  else
    summary+="  (no target‑group)"
  fi

  # colorize state
  local color="$GREEN"
  if [[ "$desired" -eq 0 ]]; then
    color="$YEL"
  elif [[ "$running" -lt "$desired" ]]; then
    color="$RED"
  fi
  echo -e "${color}${summary}${RESET}"

  # recent logs (if group exists)
  local log_group="/ecs/$svc_name"
  if timeout_cmd logs describe-log-groups --log-group-name-prefix "$log_group" \
        --query 'logGroups[0]' --output text 2>/dev/null | grep -q "$log_group"; then
    echo "── Logs (last $LOG_LINES lines) ──"
    timeout_cmd logs tail "$log_group" --since 15m --limit "$LOG_LINES" || true
  fi
  echo
}

# ─── Main ————————————————————————————————————————————————————————————
main() {
  echo "─── ECS and ALB Health check ───"
  echo "▶︎ Health run $(date -u '+%Y-%m-%dT%H:%M:%SZ') ($REGION, profile=$PROFILE)"
  echo
echo "=== Cluster: $CLUSTER ==="
  
  # fetch all services once, then iterate (throttling‑friendly)
  local svc_arns
  if ! svc_arns=$(timeout_cmd ecs list-services --cluster "$CLUSTER" --output text 2>/dev/null); then
    echo -e "${RED}✖ Failed to list services for cluster $CLUSTER${RESET}"
    exit 1
  fi

  for svc_arn in $svc_arns; do
    check_service "$svc_arn"
  done
}

main "$@"

