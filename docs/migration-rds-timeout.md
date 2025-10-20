# Migration Status: RDS Connection Timeout

## Issue
Cannot run migration directly from Codespaces because:
- RDS database is in **private VPC subnet**
- Security group only allows connections from ECS tasks
- No public internet access to database (by design, for security)

## ✅ Solution: Automatic Migration on Backend Deployment

The backend container **automatically runs migrations on startup** via `/ecs-backend/entrypoint.sh`.

### What Happens When You Deploy:

1. **Build & push updated backend image:**
   ```bash
   cd /workspaces/grid-services/ecs-backend
   ./build_and_push.sh
   ```

2. **Deploy to ECS (force new deployment):**
   ```bash
   cd /workspaces/grid-services/envs/dev
   terraform apply
   ```

3. **ECS starts new backend container with:**
   - Environment variables: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
   - Entrypoint script runs: `alembic upgrade head`
   - Migration creates `ven_acks` table
   - Backend starts normally

4. **Check migration logs:**
   ```bash
   # Get backend task ID
   aws ecs list-tasks --cluster hems-ecs-cluster --service-name backend-service
   
   # View logs
   aws logs tail /ecs/backend-service --follow
   ```

### What Gets Created:

```sql
CREATE TABLE ven_acks (
    id SERIAL PRIMARY KEY,
    ven_id VARCHAR(255) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    correlation_id VARCHAR(255),
    op VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    requested_shed_kw FLOAT,
    actual_shed_kw FLOAT,
    circuits_curtailed JSON,
    raw_payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX ix_ven_acks_ven_id ON ven_acks(ven_id);
CREATE INDEX ix_ven_acks_event_id ON ven_acks(event_id);
CREATE INDEX ix_ven_acks_correlation_id ON ven_acks(correlation_id);
CREATE INDEX ix_ven_acks_timestamp ON ven_acks(timestamp);
```

## Alternative: Manual Migration from ECS Task

If you need to run migration manually without deploying:

```bash
# Start an ECS Exec session to a running backend task
aws ecs execute-command \
  --cluster hems-ecs-cluster \
  --task <TASK_ID> \
  --container backend-service \
  --command "/bin/sh" \
  --interactive

# Inside the container:
alembic upgrade head
```

**Note:** ECS Exec must be enabled on the task definition.

## Deployment Steps

### 1. Build and Push Backend Image

```bash
cd /workspaces/grid-services/ecs-backend
./build_and_push.sh
```

Expected output:
```
✅ Image pushed: 923675928909.dkr.ecr.us-west-2.amazonaws.com/ecs-backend:latest
```

### 2. Force New ECS Deployment

```bash
cd /workspaces/grid-services/envs/dev

# Option A: Terraform (will update task definition and force deployment)
terraform apply -auto-approve

# Option B: AWS CLI (force immediate deployment without changing infrastructure)
aws ecs update-service \
  --cluster hems-ecs-cluster \
  --service backend-service \
  --force-new-deployment
```

### 3. Monitor Deployment

```bash
# Watch ECS service status
watch -n 2 'aws ecs describe-services \
  --cluster hems-ecs-cluster \
  --services backend-service \
  --query "services[0].deployments[0].[status,runningCount,desiredCount]" \
  --output text'

# View backend logs (includes migration output)
aws logs tail /ecs/backend-service --follow
```

Look for migration success:
```
INFO  [alembic.runtime.migration] Running upgrade 202408051500 -> 202510200001, add ven_acks table
```

### 4. Verify Migration

```bash
# Connect to RDS from a bastion host or ECS Exec session
psql -h opendar-aurora.cluster-cfe6sou489x3.us-west-2.rds.amazonaws.com \
     -U ecs_backend_admin \
     -d ecsbackenddb

# Check if table exists
\dt ven_acks

# View table structure
\d ven_acks
```

## Files Changed

1. **`ecs-backend/app/models/ven_ack.py`** - New VenAck model
2. **`ecs-backend/app/models/__init__.py`** - Export VenAck model
3. **`ecs-backend/app/services/mqtt_consumer.py`** - Subscribe to `ven/ack/+` and persist ACKs
4. **`ecs-backend/alembic/versions/202510200001_add_ven_acks_table.py`** - Migration file
5. **`envs/dev/outputs.tf`** - Added RDS database outputs

## Testing After Deployment

Once deployed, test the full flow:

```bash
# 1. Create DR event via backend API
curl -X POST "http://backend-alb-948465488.us-west-2.elb.amazonaws.com/api/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "startTime": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "endTime": "'$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)'",
    "requestedReductionKw": 5.0,
    "status": "active"
  }'

# 2. EventCommandService publishes MQTT command to VEN

# 3. VEN sends ACK with circuit details

# 4. Query database to verify ACK was stored:
# (From ECS Exec session or bastion)
psql -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -c \
  "SELECT ven_id, event_id, actual_shed_kw, 
          jsonb_array_length(circuits_curtailed::jsonb) as circuits_count 
   FROM ven_acks 
   ORDER BY created_at DESC 
   LIMIT 5;"
```

## Summary

✅ **Migration file created**: `202510200001_add_ven_acks_table.py`  
✅ **Backend auto-runs migrations**: `entrypoint.sh` already configured  
✅ **RDS outputs added**: Can get DB credentials from Terraform  
⏳ **Next step**: Build & deploy backend image  

The migration will run automatically when the new backend container starts in ECS!
