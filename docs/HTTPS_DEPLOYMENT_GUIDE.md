# HTTPS Deployment Guide

This guide provides comprehensive instructions for deploying HappyRobot FDE API with HTTPS support in both local development and production environments.

## Quick Start - Local Development

### Prerequisites
- Docker and Docker Compose installed
- Git repository cloned
- `.env` file configured (see `.env.example`)

### 1. Local HTTPS Setup

```bash
# 1. Generate self-signed certificates (if not already present)
./scripts/generate-certs.sh

# 2. Set HTTPS configuration
echo "ENABLE_HTTPS=true" >> .env

# 3. Start all services
docker-compose up --build

# 4. Test the setup
./scripts/test-https.sh
```

### 2. Verify Services

- **HTTPS API**: https://localhost (redirects to docs)
- **API Documentation**: https://localhost/api/v1/docs
- **Health Check**: https://localhost/api/v1/health
- **HTTP Redirect**: http://localhost (redirects to HTTPS)

## Architecture Overview

```
Internet/Load Balancer → Nginx (SSL/TLS Termination) → FastAPI Application
                      ↓
              Security Headers Applied
              Rate Limiting
              SSL Certificate Management
```

### Security Layers

1. **Nginx Layer** (Primary Security):
   - SSL/TLS termination
   - HTTP to HTTPS redirect
   - Security headers (HSTS, CSP, etc.)
   - Rate limiting
   - Request filtering

2. **FastAPI Layer** (Application Security):
   - API key authentication
   - CORS configuration
   - Application-level security headers
   - Request validation

## Environment Configuration

### Required Environment Variables

```bash
# Security Configuration
ENABLE_HTTPS=true              # Enable HSTS headers in FastAPI
API_KEY=your-secure-api-key    # API authentication key

# Database Configuration
POSTGRES_DB=happyrobot
POSTGRES_USER=happyrobot
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=postgres         # Use 'localhost' for local non-Docker setup

# AWS Configuration (for production)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=eu-south-2
```

### Local Development Settings

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration for local development
ENABLE_HTTPS=true
API_KEY=dev-local-api-key
POSTGRES_HOST=postgres  # For Docker setup
```

## SSL Certificate Management

### Local Development (Self-Signed)

```bash
# Generate self-signed certificate
./scripts/generate-certs.sh

# Certificates are stored in ./certs/
# - server.crt (certificate)
# - server.key (private key)
```

### Production (AWS/Let's Encrypt)

For production deployment, use proper SSL certificates:

1. **AWS Certificate Manager** (Recommended for AWS deployments)
2. **Let's Encrypt** (Free certificates)
3. **Commercial SSL certificates**

## Testing Commands

### Comprehensive Testing

```bash
# Run all HTTPS tests
./scripts/test-https.sh

# Test with custom deployment URL
DEPLOYED_URL=https://your-api.domain.com ./scripts/test-https.sh

# Test with custom API key
API_KEY=your-api-key ./scripts/test-https.sh
```

### Manual Testing

```bash
# Test HTTPS health endpoint
curl -k https://localhost/api/v1/health

# Test security headers
curl -k -I https://localhost/api/v1/health

# Test HTTP to HTTPS redirect
curl -I http://localhost/api/v1/health

# Test authenticated endpoint
curl -k -H "X-API-Key: your-key" https://localhost/api/v1/loads/search \
  -H "Content-Type: application/json" \
  -d '{"origin_city": "test", "destination_city": "test"}'
```

### Expected Security Headers

When testing via HTTPS (nginx), you should see:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; ...
```

## AWS Production Deployment

### 1. Infrastructure Setup (Pulumi)

```bash
# Navigate to infrastructure directory
cd infrastructure/pulumi

# Install dependencies
npm install

# Login to Pulumi
pulumi login

# Select or create stack
pulumi stack select happyrobot-prod

# Deploy infrastructure
pulumi up
```

### 2. SSL Certificate Setup

```bash
# Request certificate via AWS ACM
aws acm request-certificate \
  --domain-name api.your-domain.com \
  --validation-method DNS \
  --region eu-south-2

# Add DNS validation records to your domain
# Wait for certificate validation
```

### 3. Application Deployment

```bash
# Set production environment variables
export ENABLE_HTTPS=true
export API_KEY=your-production-api-key
export POSTGRES_HOST=your-rds-endpoint

# Deploy via Pulumi (automatically uses ECS)
pulumi up
```

### 4. Domain Configuration

```bash
# Point your domain to the Application Load Balancer
# Update DNS A/CNAME records:
# api.your-domain.com -> your-alb.eu-south-2.elb.amazonaws.com
```

## Troubleshooting

### Common Issues

1. **Certificate Errors**
   ```bash
   # Self-signed certificate warnings are normal for local development
   # Use -k flag with curl or add certificate to trust store
   curl -k https://localhost/api/v1/health
   ```

2. **Port 443 Already in Use**
   ```bash
   # Check what's using port 443
   sudo netstat -tlnp | grep :443

   # Stop conflicting services or change nginx port mapping
   # Edit docker-compose.yml: "8443:443" instead of "443:443"
   ```

3. **Health Check Failures**
   ```bash
   # Check container status
   docker ps

   # Check nginx logs
   docker logs happyrobot-nginx

   # Check API logs
   docker logs happyrobot-api

   # Restart services
   docker-compose restart
   ```

4. **Missing Security Headers**
   ```bash
   # Headers should come from nginx layer
   curl -k -I https://localhost/api/v1/health | grep -i "x-frame\|strict"

   # If missing, check nginx configuration
   docker exec happyrobot-nginx cat /etc/nginx/nginx.conf
   ```

5. **Database Connection Issues**
   ```bash
   # Verify database is running
   docker ps | grep postgres

   # Check database logs
   docker logs happyrobot-postgres

   # Test connection
   docker exec happyrobot-api python -c "from src.config.settings import settings; print(settings.get_async_database_url)"
   ```

### Log Analysis

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f happyrobot-api
docker-compose logs -f happyrobot-nginx
docker-compose logs -f postgres

# Follow logs in real-time
docker-compose logs -f --tail=50
```

### Performance Monitoring

```bash
# Check container resource usage
docker stats

# Monitor nginx access logs
docker logs happyrobot-nginx -f | grep -v "health"

# Monitor API response times
curl -w "@curl-format.txt" -s -o /dev/null https://localhost/api/v1/health
```

## Security Considerations

### Production Checklist

- [ ] Use proper SSL certificates (not self-signed)
- [ ] Set strong, unique API keys
- [ ] Configure proper CORS origins (not `*`)
- [ ] Enable HSTS headers (`ENABLE_HTTPS=true`)
- [ ] Use secure database passwords
- [ ] Enable AWS CloudTrail for auditing
- [ ] Configure AWS WAF for additional protection
- [ ] Set up monitoring and alerting
- [ ] Regular security updates and patches

### Network Security

```bash
# Firewall rules (production)
# Allow only necessary ports:
# - 80 (HTTP - redirects to HTTPS)
# - 443 (HTTPS)
# - 22 (SSH - from specific IPs only)

# AWS Security Groups
# Inbound:
# - Port 80: 0.0.0.0/0
# - Port 443: 0.0.0.0/0
# - Port 22: Your-IP/32
#
# Outbound:
# - All traffic (for API dependencies)
```

## Monitoring and Maintenance

### Health Checks

```bash
# Automated health check script
#!/bin/bash
ENDPOINTS=(
  "https://your-api.domain.com/api/v1/health"
  "https://your-api.domain.com/api/v1/docs"
)

for endpoint in "${ENDPOINTS[@]}"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
  if [ "$status" = "200" ]; then
    echo "✓ $endpoint"
  else
    echo "✗ $endpoint (HTTP $status)"
  fi
done
```

### Certificate Renewal

```bash
# AWS ACM certificates auto-renew
# For Let's Encrypt:
certbot renew --dry-run

# For manual certificates, set up renewal reminders
# Certificates typically expire after 90 days (Let's Encrypt) or 1 year
```

### Backup and Recovery

```bash
# Database backup
docker exec happyrobot-postgres pg_dump -U happyrobot happyrobot > backup.sql

# Certificate backup
cp certs/server.crt certs/server.key /secure/backup/location/

# Configuration backup
cp .env docker-compose.yml nginx/nginx.conf /secure/backup/location/
```

## Advanced Configuration

### Custom SSL Configuration

```nginx
# Enhanced SSL configuration for nginx.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
```

### Rate Limiting Customization

```nginx
# Custom rate limiting in nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=health:10m rate=200r/m;
limit_req_zone $binary_remote_addr zone=docs:10m rate=10r/m;

# Apply to specific locations
location /api/ {
    limit_req zone=api burst=50 nodelay;
    # ... rest of configuration
}
```

### Load Balancing (Multi-Instance)

```yaml
# docker-compose.yml for multiple API instances
services:
  happyrobot-api-1:
    # ... API configuration
  happyrobot-api-2:
    # ... API configuration

  nginx:
    # Update upstream configuration
    # Multiple backend servers for load balancing
```

## Support and Updates

### Getting Help

1. Check this documentation first
2. Review container logs: `docker-compose logs`
3. Test with the provided scripts: `./scripts/test-https.sh`
4. Check GitHub issues and documentation
5. Contact the development team

### Staying Updated

```bash
# Update Docker images
docker-compose pull

# Rebuild with latest changes
docker-compose up --build

# Update infrastructure
cd infrastructure/pulumi && pulumi up
```

---

## Quick Reference Commands

```bash
# Start services
docker-compose up --build

# Test HTTPS setup
./scripts/test-https.sh

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart happyrobot-nginx

# Check container health
docker ps

# Access database
docker exec -it happyrobot-postgres psql -U happyrobot -d happyrobot

# Generate new certificates
./scripts/generate-certs.sh

# Deploy to AWS
cd infrastructure/pulumi && pulumi up
```

This guide provides a complete reference for HTTPS deployment and management of the HappyRobot FDE API. For specific issues not covered here, refer to the individual component documentation or contact the development team.
