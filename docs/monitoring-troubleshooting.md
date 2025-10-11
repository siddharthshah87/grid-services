# Monitoring and Troubleshooting Guide

This guide covers monitoring the Grid Services infrastructure and troubleshooting common issues across all system components.

## Monitoring Overview

The Grid Services platform uses comprehensive monitoring across multiple layers:

- **Infrastructure**: ECS, RDS, ALB, IoT Core metrics
- **Application**: Service health, API performance, error rates  
- **Network**: Connectivity, latency, throughput
- **Security**: Access patterns, certificate status, failed attempts

## CloudWatch Monitoring

### Log Groups and Streams
```bash
# List all Grid Services log groups
aws logs describe-log-groups \
  --log-group-name-prefix "/ecs/grid-services"

# Common log groups:
/ecs/grid-services-dev/backend
/ecs/grid-services-dev/grid-event-gateway
/ecs/grid-services-dev/volttron-ven
/ecs/grid-services-dev/frontend
```

### Viewing Real-Time Logs
```bash
# Follow logs in real-time
aws logs tail "/ecs/grid-services-dev/backend" --follow

# Filter logs by pattern
aws logs filter-log-events \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --filter-pattern "ERROR"

# View logs from specific time range
aws logs filter-log-events \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --end-time $(date +%s)000
```

### Log Analysis Queries
```bash
# Find application errors
aws logs start-query \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --start-time $(date -d '24 hours ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'

# Monitor API response times
aws logs start-query \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /response_time/ | stats avg(response_time) by bin(5m)'
```

### CloudWatch Metrics

#### ECS Service Metrics
```bash
# CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=backend-service Name=ClusterName,Value=grid-services-dev \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# Memory utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=backend-service Name=ClusterName,Value=grid-services-dev \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

#### ALB Metrics
```bash
# Request count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/grid-event-gateway-alb/1234567890abcdef \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Response time
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/grid-event-gateway-alb/1234567890abcdef \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

## ECS Service Monitoring

### Service Health Checks
```bash
# Check service status
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service volttron-service grid-event-gateway-service

# View service events (last 10)
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service \
  --query 'services[0].events[:10]'

# Check task health
aws ecs list-tasks --cluster grid-services-dev --service-name backend-service
aws ecs describe-tasks --cluster grid-services-dev --tasks <task-arn>
```

### Task-Level Monitoring
```bash
# Get task definition details
aws ecs describe-task-definition --task-definition backend-task

# Check task status and health
aws ecs describe-tasks \
  --cluster grid-services-dev \
  --tasks <task-arn> \
  --query 'tasks[0].{Status:lastStatus,Health:healthStatus,CPU:cpu,Memory:memory}'

# View task stop reasons
aws ecs describe-tasks \
  --cluster grid-services-dev \
  --tasks <task-arn> \
  --query 'tasks[0].stoppedReason'
```

## Application Load Balancer Monitoring

### Target Health Checks
```bash
# Check target group health
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names grid-event-gateway-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

TG_ARN=$(aws elbv2 describe-target-groups \
  --load-balancer-arn $ALB_ARN \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

aws elbv2 describe-target-health --target-group-arn $TG_ARN
```

### ALB Access Logs
```bash
# Enable ALB access logs (if not already enabled)
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn $ALB_ARN \
  --attributes Key=access_logs.s3.enabled,Value=true \
               Key=access_logs.s3.bucket,Value=my-alb-logs-bucket

# Analyze access logs from S3
aws s3 ls s3://my-alb-logs-bucket/AWSLogs/<account-id>/elasticloadbalancing/
```

## Database Monitoring

### RDS Performance Metrics
```bash
# Database connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=grid-services-dev-db \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=grid-services-dev-db \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

### Database Connection Testing
```bash
# Test database connectivity from local machine
DB_ENDPOINT=$(terraform output -raw db_endpoint)
psql -h $DB_ENDPOINT -U postgres -d grid_services -c "SELECT version();"

# Test from ECS task (exec into running container)
aws ecs execute-command \
  --cluster grid-services-dev \
  --task <task-arn> \
  --container backend \
  --command "/bin/bash" \
  --interactive
```

## IoT Core Monitoring

### MQTT Message Monitoring
```bash
# Check IoT Core metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name PublishIn.Success \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Monitor rule executions
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name RuleMessageCount \
  --dimensions Name=RuleName,Value=mqtt-forward-rule \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Device Shadow Monitoring
```bash
# Monitor shadow updates
./scripts/ven_shadow_get.py --ven-id $THING_NAME --endpoint $IOT_ENDPOINT

# Check Thing connectivity
aws iot describe-thing --thing-name $THING_NAME

# List device certificates
aws iot list-thing-principals --thing-name $THING_NAME
```

### MQTT Topic Testing
```bash
# Listen to MQTT topics
./scripts/ven_acks_listen.py --ven-id $THING_NAME --endpoint $IOT_ENDPOINT

# Publish test commands
./scripts/ven_cmd_publish.py \
  --ven-id $THING_NAME \
  --endpoint $IOT_ENDPOINT \
  --op ping
```

## Application-Level Monitoring

### API Health Checks
```bash
# Backend API health
curl -f https://api.gridcircuit.link/health
curl -f https://api.gridcircuit.link/stats/network

# VEN Agent health  
curl -f https://sim.gridcircuit.link/health
curl -f https://sim.gridcircuit.link/live

# Grid-Event Gateway health
curl -f https://vtn.gridcircuit.link/health
```

### Real-Time VEN Monitoring
```bash
# Monitor VEN live data
./scripts/ven_http_live.py --base-url $VEN_URL --interval 2

# Check VEN configuration
curl -s $VEN_URL/config | jq '.'

# Monitor VEN circuits
curl -s $VEN_URL/circuits | jq '.'
```

### Performance Testing
```bash
# Load test backend API
curl -w "@curl-format.txt" -o /dev/null -s "https://api.gridcircuit.link/stats/network"

# Create curl-format.txt:
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

## Troubleshooting Common Issues

### Service Deployment Failures

#### Issue: ECS Service Not Starting
```bash
# Check service events
aws ecs describe-services \
  --cluster grid-services-dev \
  --services backend-service \
  --query 'services[0].events[:5]'

# Check task definition
aws ecs describe-task-definition --task-definition backend-task

# Check task logs
aws logs filter-log-events \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --start-time $(date -d '30 minutes ago' +%s)000
```

**Common Causes**:
- Image pull failures (check ECR permissions)
- Environment variable issues (check Secrets Manager)
- Resource limits (CPU/memory constraints)
- Network configuration (security groups, subnets)

#### Issue: Health Check Failures
```bash
# Check ALB target health
aws elbv2 describe-target-health --target-group-arn $TG_ARN

# Test health endpoint directly
curl -v http://<ecs-task-ip>:8000/health
```

**Common Causes**:
- Application startup time exceeding health check grace period
- Health endpoint returning non-200 status
- Network connectivity issues (security groups)
- Application dependencies not ready (database, external services)

### Database Connection Issues

#### Issue: Database Connection Timeouts
```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier grid-services-dev-db

# Test database connectivity
telnet $DB_ENDPOINT 5432

# Check security group rules
aws ec2 describe-security-groups --group-ids <db-security-group-id>
```

**Common Causes**:
- Security group not allowing ECS task access
- Database instance stopped or in maintenance
- Connection pool exhaustion
- Network ACL restrictions

#### Issue: Database Performance Problems
```bash
# Check slow query logs
aws rds describe-db-log-files --db-instance-identifier grid-services-dev-db

# Download slow query log
aws rds download-db-log-file-portion \
  --db-instance-identifier grid-services-dev-db \
  --log-file-name error/postgresql.log.2023-10-11-12
```

### IoT Core Communication Issues

#### Issue: MQTT Connection Failures
```bash
# Check certificate validity
openssl x509 -in client.crt -text -noout

# Test MQTT connection
mosquitto_pub -h $IOT_ENDPOINT -p 8883 \
  --cafile ca.crt --cert client.crt --key client.key \
  -t test/topic -m "test message" -d

# Check IoT policies
aws iot list-attached-policies --target <certificate-arn>
```

**Common Causes**:
- Certificate expired or invalid
- IoT policy insufficient permissions
- Network connectivity issues
- Incorrect endpoint or port

#### Issue: Device Shadow Not Updating
```bash
# Check shadow permissions
aws iot get-policy --policy-name VENPolicy

# Test shadow access
aws iot-data get-thing-shadow --thing-name $THING_NAME shadow.json

# Check for shadow errors in CloudWatch
aws logs filter-log-events \
  --log-group-name "AWSIotLogsV2" \
  --filter-pattern "ERROR"
```

### Load Balancer Issues

#### Issue: 502/503 Errors from ALB
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn $TG_ARN

# Check ALB logs
aws s3 cp s3://alb-logs-bucket/AWSLogs/<account-id>/elasticloadbalancing/us-west-2/2023/10/11/ . --recursive

# Analyze error patterns
grep "502\|503" *.log | head -20
```

**Common Causes**:
- No healthy targets in target group
- Application returning errors
- Target group health check misconfiguration
- Network connectivity issues

#### Issue: SSL/TLS Certificate Problems
```bash
# Check certificate status
aws acm describe-certificate --certificate-arn $CERT_ARN

# Test SSL configuration
openssl s_client -connect gridcircuit.link:443 -servername gridcircuit.link

# Check certificate validation
dig gridcircuit.link CNAME
```

### Performance Issues

#### Issue: High Response Times
```bash
# Check service metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=$ALB_ARN \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# Check database performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReadLatency \
  --dimensions Name=DBInstanceIdentifier,Value=grid-services-dev-db \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

**Optimization Strategies**:
- Scale ECS services horizontally
- Increase ECS task CPU/memory
- Optimize database queries
- Add database read replicas
- Implement application caching

## Alerting and Notifications

### CloudWatch Alarms
```bash
# Create CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "ECS-Backend-HighCPU" \
  --alarm-description "Backend service high CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=backend-service Name=ClusterName,Value=grid-services-dev \
  --evaluation-periods 2

# Create database connection alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "RDS-HighConnections" \
  --alarm-description "Database high connection count" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=grid-services-dev-db \
  --evaluation-periods 2
```

### SNS Notifications
```bash
# Create SNS topic for alerts
aws sns create-topic --name grid-services-alerts

# Subscribe email to topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456789012:grid-services-alerts \
  --protocol email \
  --notification-endpoint admin@example.com
```

## Log Aggregation and Analysis

### Centralized Logging
```bash
# Set up log forwarding to external systems
# Example: Forward to Elasticsearch/OpenSearch

# Create log destination
aws logs create-destination \
  --destination-name "ElasticsearchDestination" \
  --target-arn "arn:aws:es:us-west-2:123456789012:domain/logging/*" \
  --role-arn "arn:aws:iam::123456789012:role/CloudWatchLogsRole"

# Create subscription filter
aws logs put-subscription-filter \
  --log-group-name "/ecs/grid-services-dev/backend" \
  --filter-name "ElasticsearchFilter" \
  --filter-pattern "[timestamp, request_id, level=\"ERROR\", ...]" \
  --destination-arn "arn:aws:logs:us-west-2:123456789012:destination:ElasticsearchDestination"
```

### Custom Metrics
```python
# Example: Custom application metrics
import boto3

cloudwatch = boto3.client('cloudwatch')

# Publish custom metric
cloudwatch.put_metric_data(
    Namespace='GridServices/Application',
    MetricData=[
        {
            'MetricName': 'VENConnectionCount',
            'Value': active_ven_count,
            'Unit': 'Count',
            'Dimensions': [
                {
                    'Name': 'Environment',
                    'Value': 'dev'
                }
            ]
        }
    ]
)
```

## Automated Monitoring Scripts

### Health Check Script
```bash
#!/bin/bash
# scripts/health_check_all.sh

set -e

echo "Checking Grid Services Health..."

# Backend API
if curl -f -s https://api.gridcircuit.link/health > /dev/null; then
    echo "✓ Backend API: Healthy"
else
    echo "✗ Backend API: Unhealthy"
fi

# VEN Agent
if curl -f -s https://sim.gridcircuit.link/health > /dev/null; then
    echo "✓ VEN Agent: Healthy"
else
    echo "✗ VEN Agent: Unhealthy"
fi

# Database
if psql -h $DB_ENDPOINT -U postgres -d grid_services -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✓ Database: Healthy"
else
    echo "✗ Database: Unhealthy"
fi

# IoT Core
if aws iot describe-endpoint --endpoint-type iot:Data-ATS > /dev/null; then
    echo "✓ IoT Core: Healthy"
else
    echo "✗ IoT Core: Unhealthy"
fi
```

### Monitoring Dashboard
```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "GridServicesDashboard" \
  --dashboard-body file://dashboard.json

# dashboard.json content:
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", "ServiceName", "backend-service", "ClusterName", "grid-services-dev"],
          [".", "MemoryUtilization", ".", ".", ".", "."]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "ECS Service Metrics"
      }
    }
  ]
}
```

This comprehensive monitoring and troubleshooting guide provides the tools and procedures needed to maintain the Grid Services infrastructure effectively.