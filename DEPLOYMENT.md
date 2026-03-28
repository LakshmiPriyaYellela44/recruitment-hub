# Deployment Guide

## 🚀 Production Deployment Checklist

- [ ] Environment variables configured
- [ ] Database backed up
- [ ] SSL certificates ready
- [ ] API keys stored securely
- [ ] Frontend build optimized
- [ ] Backend dependencies updated
- [ ] All tests passing
- [ ] Error tracking configured
- [ ] Monitoring setup
- [ ] Load balancer configured

---

## 🐳 Docker Deployment (Recommended)

### Prerequisites
- Docker installed (version 20+)
- Docker Compose installed (version 2+)
- PostgreSQL installed or use container version

### Quick Start with Docker Compose

```bash
# Navigate to project root
cd d:\recruitment

# Create .env file for production
cp .env.example .env
# Edit .env with production values:
# - DATABASE_URL: Full PostgreSQL connection string
# - JWT_SECRET_KEY: Strong random key
# - AWS_MOCK_ENABLED: false (use real AWS)
# - VITE_API_URL: Production API URL

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Docker Compose Services

```yaml
services:
  postgres:
    - Database service
    - Port: 5432
    - Volume: persisted data
  
  backend:
    - FastAPI application
    - Port: 8000
    - Depends on: postgres
    - Health check: /health endpoint
  
  frontend:
    - React application
    - Port: 3000
    - Reverse proxy: Nginx (optional)
```

---

## ☁️ Cloud Deployment Options

### 1. AWS Deployment

#### Option A: App Runner (Simplest)

```bash
# 1. Build Docker image
docker build -t recruitment-backend:latest ./backend
docker build -t recruitment-frontend:latest ./frontend

# 2. Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag recruitment-backend:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitment-backend:latest
docker tag recruitment-frontend:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitment-frontend:latest

docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitment-backend:latest
docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitment-frontend:latest

# 3. Create App Runner services in AWS Console
# - Backend on App Runner
# - Frontend on App Runner  
# - Connect with security groups
```

#### Option B: ECS Fargate

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name recruitment

# Register task definitions
# Push Docker images to ECR
# Create services and tasks
# Configure load balancer
```

#### Option C: Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize environment
eb init -p docker recruitment

# Deploy
eb create production-env
eb deploy
```

### 2. Heroku Deployment

```bash
# Install Heroku CLI
npm install -g heroku

# Login to Heroku
heroku login

# Create app
heroku create recruitment-platform

# Set environment variables
heroku config:set VITE_API_URL=https://recruitment-api.herokuapp.com/api
heroku config:set DATABASE_URL=postgresql://...

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### 3. DigitalOcean App Platform

```bash
# Link repository to DigitalOcean
# Configure in DigitalOcean Console:
# - Backend service (HTTP)
# - Frontend service (HTTP)
# - PostgreSQL database
# Auto-deploys on git push
```

### 4. Vercel (Frontend Only)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
vercel --prod

# Configure environment
vercel env add VITE_API_URL https://api.recruitment.app

# Set continuous deployment
# - Connected to GitHub
# - Auto-deploy on push
```

### 5. Azure Container Instances

```bash
# Create resource group
az group create --name recruitment --location eastus

# Push to ACR
az acr build --registry recruitmentacr --image recruitment-backend:latest ./backend
az acr build --registry recruitmentacr --image recruitment-frontend:latest ./frontend

# Deploy container instance
az container create \
  --resource-group recruitment \
  --name recruitment-backend \
  --image recruitmentacr.azurecr.io/recruitment-backend:latest \
  --ports 8000 \
  --environment-variables DATABASE_URL=$DATABASE_URL
```

---

## 🔧 Infrastructure as Code

### Terraform Example (AWS)

```hcl
# main.tf
provider "aws" {
  region = "us-east-1"
}

# RDS PostgreSQL
resource "aws_db_instance" "recruitment" {
  identifier     = "recruitment-db"
  engine         = "postgres"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  username       = var.db_username
  password       = var.db_password
  skip_final_snapshot = false
}

# Secrets Manager for sensitive data
resource "aws_secretsmanager_secret" "jwt_key" {
  name = "recruitment/jwt-secret"
}

# Application Load Balancer
resource "aws_lb" "recruitment" {
  name               = "recruitment-lb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.subnets
}

# Deploy with Terraform
# terraform init
# terraform plan
# terraform apply
```

### CloudFormation Example (AWS)

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'

Resources:
  RecruitmentDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: recruitment-db
      Engine: postgres
      DBInstanceClass: db.t3.micro
      MasterUsername: admin
      MasterUserPassword: !Ref DBPassword

  RecruitmentSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: recruitment/jwt-secret
      SecretString: !Ref JWTSecret

Parameters:
  DBPassword:
    Type: String
    NoEcho: true
  JWTSecret:
    Type: String
    NoEcho: true

# Deploy: aws cloudformation create-stack --template-body file://template.yaml
```

### Bicep Example (Azure)

```bicep
// main.bicep
param location string = resourceGroup().location
param environment string = 'production'

resource postgres 'Microsoft.DBforPostgreSQL/servers@2017-12-01' = {
  name: 'recruitment-db-${environment}'
  location: location
  properties: {
    administratorLogin: 'pgadmin'
    administratorLoginPassword: 'SecurePassword123!'
    version: '11'
    sslEnforcement: 'ENABLED'
  }
}

resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: 'recruitment-api-${environment}'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
  }
}

// Deploy: az deployment group create --template-file main.bicep
```

---

## 📊 Monitoring & Logging

### Application Monitoring

```python
# Add to backend for monitoring
from prometheus_client import Counter, Histogram
import time

request_count = Counter(
  'http_requests_total',
  'Total HTTP requests'
)

request_duration = Histogram(
  'http_request_duration_seconds',
  'HTTP request duration'
)

@app.middleware("http")
async def track_metrics(request, call_next):
  start_time = time.time()
  request_count.inc()
  
  response = await call_next(request)
  
  duration = time.time() - start_time
  request_duration.observe(duration)
  
  return response
```

### Logging Service

```python
# Configure structured logging
import structlog

logger = structlog.get_logger()

logger.info(
  "user_login",
  user_id="uuid",
  timestamp="2024-01-15T10:30:00",
  status="success"
)
```

### Cloud Monitoring

**AWS CloudWatch**
```bash
# View logs
aws logs tail /aws/lambda/recruitment-resume-worker --follow

# Create metrics
aws cloudwatch put-metric-data \
  --namespace recruitment \
  --metric-name ResumeParsed \
  --value 1
```

**Azure Monitor**
```bash
# Configure Application Insights
# View metrics in Azure Portal
# Set up alerts for critical metrics
```

---

## 🔐 Security Hardening

### HTTPS/SSL
```bash
# Generate certificate (Let's Encrypt)
certbot certonly --standalone -d recruitment.app

# Configure in Nginx
server {
  listen 443 ssl http2;
  ssl_certificate /path/to/cert;
  ssl_certificate_key /path/to/key;
  ssl_protocols TLSv1.2 TLSv1.3;
}

# Force HTTPS
server {
  listen 80;
  return 301 https://$server_name$request_uri;
}
```

### Environment Secrets
```bash
# Use .env with strong values
JWT_SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32)

# Never commit to version control
echo '.env' >> .gitignore

# Use secrets manager in production
# AWS Secrets Manager / Azure Key Vault / HashiCorp Vault
```

### Database Security
```sql
-- Create restricted user
CREATE USER recruitment_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE recruitment_db TO recruitment_app;
GRANT USAGE ON SCHEMA public TO recruitment_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO recruitment_app;

-- Enable SSL
require_secure_ssl = 1

-- Setup backups
pg_dump recruitment_db | gzip > backup-$(date +%Y%m%d).sql.gz
```

### API Security
```python
# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login():
  pass

# CORS configuration for production
app.add_middleware(
  CORSMiddleware,
  allow_origins=["https://recruitment.app"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
  response = await call_next(request)
  response.headers["X-Content-Type-Options"] = "nosniff"
  response.headers["X-Frame-Options"] = "DENY"
  response.headers["X-XSS-Protection"] = "1; mode=block"
  return response
```

---

## 📈 Scaling Considerations

### Horizontal Scaling

```
Load Balancer
├── Backend Instance 1
├── Backend Instance 2
├── Backend Instance 3
└── Backend Instance N
    ↓
    Shared Database (Read Replicas)
    ↓
    Cache Layer (Redis)
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_experiences_years ON experiences(years);

-- Connection pooling
-- Use pgBouncer or RDS Proxy

-- Read replicas
-- Distribute read-heavy queries
```

### Caching Strategy

```python
# Redis caching
from redis import Redis

redis_client = Redis(host='localhost', port=6379)

@app.get("/skills")
async def get_skills():
  cached = redis_client.get("skills_list")
  if cached:
    return json.loads(cached)
  
  skills = await get_skills_from_db()
  redis_client.setex("skills_list", 3600, json.dumps(skills))
  return skills
```

---

## 📋 Backup & Disaster Recovery

### Database Backups

```bash
# Automated daily backups
# AWS RDS automatic backups (35-day retention)
# Azure Database automatic backups (35-day retention)

# Manual backup
pg_dump recruitment_db > backup.sql

# Restore from backup
psql recruitment_db < backup.sql

# Backup to S3
pg_dump recruitment_db | gzip | \
  aws s3 cp - s3://recruitment-backups/backup-$(date +%Y%m%d).sql.gz
```

### Disaster Recovery Plan

```
1. Database Failure
   - Failover to read replica (automatic in RDS)
   - Restore from backup if needed

2. Application Crash
   - Health check triggers restart
   - Auto-scaling spins up new instances

3. Data Center Outage
   - Multi-region deployment
   - Failover to alternate region

4. Ransomware Attack
   - Isolated backup restoration
   - Point-in-time recovery
```

---

## ✅ Post-Deployment Checklist

- [ ] Health checks working
- [ ] Database connectivity verified
- [ ] API endpoints responding
- [ ] Frontend loading correctly
- [ ] Authentication working
- [ ] Email sending functional
- [ ] Resume parsing working
- [ ] Logs being collected
- [ ] Metrics being tracked
- [ ] Alerts configured
- [ ] Backups running
- [ ] SSL certificate valid
- [ ] All tests passing
- [ ] Performance acceptable
- [ ] No critical security issues

---

## 🆘 Common Issues

### Database Connection Failed
```bash
# Check credentials
psql -U recruitment_user -d recruitment_db

# Verify DATABASE_URL
echo $DATABASE_URL

# Check network connectivity
telnet localhost 5432
```

### API Not Responding
```bash
# Check backend logs
docker-compose logs backend

# Verify port binding
lsof -i :8000

# Restart service
docker-compose restart backend
```

### Frontend Can't Connect to API
```bash
# Verify CORS settings
curl -i -X OPTIONS http://localhost:8000/api/health

# Check API URL in frontend .env
cat .env

# Test connectivity
curl http://localhost:8000/api/health
```

---

## 📞 Support & Updates

- Check logs regularly
- Update dependencies monthly
- Review security advisories
- Monitor performance metrics
- Plan capacity ahead

---

**Ready to deploy! 🚀**
