# HappyRobot FDE - Deployment Guide

## Table of Contents
- [Local Development Deployment](#local-development-deployment)
- [AWS Cloud Deployment](#aws-cloud-deployment)
- [Troubleshooting](#troubleshooting)

## Local Development Deployment

### Prerequisites
- Docker Desktop installed and running
- Git installed
- Python 3.12+ (for backend development)

### Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd inbound-carrier-happyrobot-agent

# Copy environment variables
cp .env.example .env

# Edit .env file with your values
# Ensure these are set:
# - POSTGRES_PASSWORD (use a secure password)
# - API_KEY (for API authentication)
```

### Step 2: Start Docker Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d

# Services will be available at:
# - API: http://localhost:8000
# - PostgreSQL: localhost:5432
# - pgAdmin: http://localhost:5050 (admin@happyrobot.com/admin1234)
```

### Step 3: Initialize Database

```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Verify database setup in pgAdmin:
# 1. Navigate to http://localhost:5050
# 2. Login with admin@happyrobot.com / admin1234
# 3. Add server: postgres:5432 (happyrobot/happyrobot)
# 4. Check tables: carriers, loads, negotiations
```

### Step 4: Verify Services

```bash
# Check API health
curl http://localhost:8000/health

# Check API documentation
# Open http://localhost:8000/api/v1/docs

# Test an endpoint (with API key)
curl -X POST http://localhost:8000/api/v1/loads/search \
  -H "X-API-Key: dev-local-api-key" \
  -H "Content-Type: application/json" \
  -d '{"equipment_type": "VAN", "origin_state": "TX", "destination_state": "CA"}'

```

### Step 5: Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## AWS Cloud Deployment

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured
- Pulumi CLI installed (see installation below)
- Docker installed for building images

#### Installing Pulumi CLI

```bash
# Windows (PowerShell)
choco install pulumi
# Or download installer from https://www.pulumi.com/docs/get-started/install/

# macOS
brew install pulumi
# Or: curl -fsSL https://get.pulumi.com | sh

# Linux/WSL
curl -fsSL https://get.pulumi.com | sh

# Verify installation
pulumi version
```

### Step 1: Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region (eu-south-2)

# Verify access
aws sts get-caller-identity
```

### Step 2: Setup Pulumi

```bash
# Navigate to infrastructure directory
cd infrastructure/pulumi

# Install dependencies
npm install

# Login to Pulumi (choose one method):

# Option 1: Using Pulumi Cloud (free tier available)
pulumi login
# This will open browser for authentication

# Option 2: Using access token (for CI/CD)
export PULUMI_ACCESS_TOKEN=<your-pulumi-access-token>
pulumi login
# Get token from: https://app.pulumi.com/account/tokens

# Option 3: Local backend (no cloud account needed)
pulumi login --local
# State stored locally in ~/.pulumi

# Create new stack for FDE
pulumi stack init happyrobot-fde

# Set AWS region
pulumi config set aws:region eu-south-2
```

### Step 3: Configure Stack Variables

```bash
# Set required configuration
pulumi config set dbPassword <secure-password> --secret
pulumi config set apiKey <api-key> --secret
pulumi config set domainName <your-domain.com>

# Set environment
pulumi config set environment dev
```

### Step 4: Deploy Infrastructure

```bash
# Set passphrase for encryption (required for state security)
# The passphrase encrypts sensitive values in your Pulumi state

# - In Windows (cmd)
set PULUMI_CONFIG_PASSPHRASE=<your-secure-passphrase>

# - In Linux/Mac (bash)
export PULUMI_CONFIG_PASSPHRASE=<your-secure-passphrase>

# Note: Store this passphrase securely - you'll need it for all future operations
# For CI/CD, set PULUMI_CONFIG_PASSPHRASE in your pipeline's secret variables

# Preview changes
pulumi preview -y

# Deploy infrastructure
pulumi up -s inbound-carrier-agent -y

# This will create:
# - VPC with public/private subnets
# - RDS PostgreSQL instance
# - ECS Cluster with Fargate services
# - Application Load Balancer
# - ECR repositories
# - CloudWatch logs and monitoring
```

### Step 5: Build and Push Docker Images

```bash
# Get ECR repository URLs from Pulumi output
pulumi stack output ecrApiUrl

# Login to ECR
aws ecr get-login-password --region eu-south-2 | \
  docker login --username AWS --password-stdin <ecr-url>

# Build and push API image
docker build -t happyrobot-api:latest -f Dockerfile.api .
docker tag happyrobot-api:latest <ecr-api-url>:latest
docker push <ecr-api-url>:latest

```

### Step 6: Update ECS Services

```bash
# Force new deployment with latest images
aws ecs update-service \
  --cluster happyrobot-fde \
  --service api-service \
  --force-new-deployment

# Monitor deployment
aws ecs wait services-stable \
  --cluster happyrobot-fde \
  --services api-service
```

### Step 7: Run Database Migrations

```bash
# Get RDS endpoint
pulumi stack output rdsEndpoint

# Run migrations using ECS task
aws ecs run-task \
  --cluster happyrobot-fde \
  --task-definition api-task \
  --overrides '{
    "containerOverrides": [{
      "name": "api",
      "command": ["alembic", "upgrade", "head"]
    }]
  }'
```

### Step 8: Verify Deployment

```bash
# Get ALB URL
pulumi stack output albUrl

# Check API health
curl https://<alb-url>/health

# Access services
# API: https://<alb-url>/api/v1/docs
```

### Step 9: Configure HappyRobot Platform

1. Login to HappyRobot platform
2. Create new agent "Inbound Carrier Sales"
3. Configure webhooks:
   - Load Search: `https://<alb-url>/api/v1/loads/search`
   - Negotiation: `https://<alb-url>/api/v1/negotiations/evaluate`
4. Add API key header: `X-API-Key: <your-api-key>`
5. Test voice agent workflow

## CI/CD Pipeline

The GitHub Actions workflow automatically deploys on push to main:

```yaml
# .github/workflows/deploy.yml handles:
# - Testing (pytest, npm test)
# - Building Docker images
# - Pushing to ECR
# - Running Pulumi deployment
# - Updating ECS services
```

To trigger deployment:

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

## Monitoring and Logs

### CloudWatch Dashboards

Access the dashboard at:
```bash
pulumi stack output dashboardUrl
```

Monitors:
- API response times
- Error rates
- Database connections
- ECS task health

### View Logs

```bash
# API logs
aws logs tail /ecs/happyrobot-fde/api --follow


# Database logs
aws logs tail /aws/rds/instance/happyrobot-fde --follow
```

## Troubleshooting

### Local Issues

**Docker not starting:**
```bash
# Ensure Docker Desktop is running
# Reset Docker if needed
docker system prune -a
docker compose build --no-cache
```

**Database connection errors:**
```bash
# Check postgres is running
docker compose ps

# Check logs
docker compose logs postgres

# Verify connection
docker compose exec postgres psql -U happyrobot -d happyrobot
```

**Port conflicts:**
```bash
# Check what's using ports
netstat -an | grep :8000
netstat -an | grep :3000

# Change ports in docker-compose.yml if needed
```

### AWS Issues

**ECS tasks not starting:**
```bash
# Check task logs
aws ecs describe-tasks \
  --cluster happyrobot-fde \
  --tasks <task-arn>

# Check CloudWatch logs
aws logs get-log-events \
  --log-group /ecs/happyrobot-fde/api \
  --log-stream <stream-name>
```

**Database connection from ECS:**
```bash
# Verify security groups
aws ec2 describe-security-groups \
  --group-ids <sg-id>

# Test connection from ECS task
aws ecs execute-command \
  --cluster happyrobot-fde \
  --task <task-id> \
  --container api \
  --interactive \
  --command "/bin/sh"
```

**ALB health check failures:**
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <tg-arn>

# Verify health check settings
aws elbv2 describe-target-groups \
  --target-group-arns <tg-arn>
```

## Rollback Procedures

### Local Rollback
```bash
# Stop services
docker compose down

# Checkout previous version
git checkout <previous-commit>

# Rebuild
docker compose up --build
```

### AWS Rollback
```bash
# Rollback infrastructure
pulumi stack history
pulumi stack rollback <version>

# Rollback ECS to previous task definition
aws ecs update-service \
  --cluster happyrobot-fde \
  --service api-service \
  --task-definition api-task:<previous-version>
```

## Security Notes

1. **Never commit secrets** - Use environment variables and Pulumi secrets
2. **Rotate API keys regularly** - Update in Pulumi config
3. **Enable AWS GuardDuty** - For threat detection
4. **Use least privilege IAM** - Restrict permissions
5. **Enable RDS encryption** - Already configured in Pulumi
6. **Regular backups** - Configure RDS automated backups

## Support

For issues or questions:
- Check logs first (CloudWatch, Docker logs)
- Review error messages carefully
- Consult architecture documentation in `docs/`
- Contact DevOps team for infrastructure issues

## Cost Optimization

Estimated monthly costs (AWS):
- Development: ~$85-95
- Production: ~$250-350

To reduce costs:
- Use smaller instance types for dev
- Enable auto-scaling with proper limits
- Clean up unused resources
- Use Reserved Instances for production

---

Last Updated: 2024-08-14
Version: 1.0.0
