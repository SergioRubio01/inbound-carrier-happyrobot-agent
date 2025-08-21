# HTTPS Implementation Plan for HappyRobot FDE API

## Executive Summary

This document outlines a comprehensive plan to implement HTTPS support for the HappyRobot FDE Inbound Carrier Sales API across both local development and AWS production environments. The implementation will enhance security by encrypting all API communications while maintaining the existing authentication mechanisms and architectural patterns.

**Key Objectives:**
- Enable HTTPS in local development using self-signed certificates
- Configure HTTPS in AWS using AWS Certificate Manager (ACM)
- Maintain backward compatibility during transition
- Ensure minimal disruption to existing HappyRobot platform integrations

**Estimated Implementation Time:** 4-6 hours
**Risk Level:** Low to Medium
**Required Expertise:** DevOps, AWS, Docker, FastAPI

---

## Current Security State Assessment

### Existing Security Mechanisms
1. **API Authentication:**
   - API Key-based authentication via headers (`X-API-Key` or `Authorization: ApiKey <key>`)
   - Middleware-based protection for all endpoints except health checks
   - Environment-specific API keys

2. **AWS Infrastructure:**
   - Application Load Balancer (ALB) with HTTP listener on port 80
   - Optional HTTPS listener on port 443 (infrastructure exists but not configured)
   - Security groups properly configured for ports 80 and 443
   - WAF protection available for production environments

3. **Local Development:**
   - HTTP-only communication on port 8000
   - Docker Compose setup without TLS configuration
   - No certificate management infrastructure

### Security Gaps Identified
- **Plain-text API keys** transmitted over HTTP in local development
- **No HTTPS enforcement** at the application level
- **Missing security headers** (HSTS, CSP, etc.)
- **No certificate automation** for local development

---

## Implementation Plan

### Phase 1: Local Development HTTPS

#### 1.1 Self-Signed Certificate Generation

**New File:** `scripts/generate-certs.sh`
```bash
#!/bin/bash
# Generate self-signed certificates for local development

CERT_DIR="./certs"
mkdir -p $CERT_DIR

# Generate private key
openssl genrsa -out $CERT_DIR/server.key 2048

# Generate certificate signing request
openssl req -new -key $CERT_DIR/server.key \
    -out $CERT_DIR/server.csr \
    -subj "/C=US/ST=State/L=City/O=HappyRobot/CN=localhost"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 \
    -in $CERT_DIR/server.csr \
    -signkey $CERT_DIR/server.key \
    -out $CERT_DIR/server.crt

# Create a combined PEM file for some services
cat $CERT_DIR/server.crt $CERT_DIR/server.key > $CERT_DIR/server.pem

echo "Certificates generated successfully in $CERT_DIR/"
```

#### 1.2 Docker Compose Modifications

**Modified File:** `docker-compose.yml`
```yaml
services:
  # Nginx reverse proxy for HTTPS termination
  nginx:
    image: nginx:alpine
    container_name: happyrobot-nginx
    restart: unless-stopped
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - happyrobot-api
    networks:
      - happyrobot-network

  happyrobot-api:
    # ... existing configuration ...
    ports:
      - "8000:8000"  # Keep for direct access if needed
    environment:
      # Add HTTPS-aware settings
      FORWARDED_ALLOW_IPS: "*"
      USE_FORWARDED_HEADERS: "true"
    # ... rest of configuration ...
```

**New File:** `nginx/nginx.conf`
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server happyrobot-api:8000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name localhost;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name localhost;

        ssl_certificate /etc/nginx/certs/server.crt;
        ssl_certificate_key /etc/nginx/certs/server.key;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $server_name;

            # WebSocket support (if needed)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

#### 1.3 FastAPI Application Updates

**Modified File:** `src/interfaces/api/app.py`
```python
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os

def create_app() -> FastAPI:
    # ... existing code ...

    # Add HTTPS redirect in non-local environments
    if settings.environment != "local":
        app.add_middleware(HTTPSRedirectMiddleware)

    # Add trusted host validation
    if settings.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )

    # ... rest of existing code ...
```

**Modified File:** `src/config/settings.py`
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # HTTPS settings
    use_https: bool = Field(default=False, alias="USE_HTTPS")
    allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1", ".happyrobot.com"],
        alias="ALLOWED_HOSTS"
    )
    forwarded_allow_ips: str = Field(default="*", alias="FORWARDED_ALLOW_IPS")
    use_forwarded_headers: bool = Field(
        default=False,
        alias="USE_FORWARDED_HEADERS"
    )

    # ... rest of existing code ...
```

### Phase 2: AWS Deployment HTTPS

#### 2.1 AWS Certificate Manager Setup

**Manual Steps Required (AWS Console):**

1. **Request ACM Certificate:**
   ```
   1. Navigate to AWS Certificate Manager
   2. Click "Request a certificate"
   3. Choose "Request a public certificate"
   4. Add domain names:
      - api.happyrobot.com
      - *.api.happyrobot.com (for subdomains)
   5. Select DNS validation
   6. Add tags: Project=happyrobot-fde, Environment=prod
   7. Review and request
   ```

2. **Domain Validation:**
   ```
   1. Add CNAME records to your DNS provider
   2. Wait for validation (usually 5-30 minutes)
   3. Note the certificate ARN
   ```

#### 2.2 Pulumi Infrastructure Updates

**Modified File:** `infrastructure/pulumi/Pulumi.happyrobot-prod.yaml`
```yaml
config:
  happyrobot-fde:environment: prod
  happyrobot-fde:apiKey: ${HAPPYROBOT_API_KEY}
  happyrobot-fde:certificateArn: arn:aws:acm:eu-south-2:xxxxx:certificate/xxxxx
  happyrobot-fde:domainName: api.happyrobot.com
  happyrobot-fde:hostedZoneId: Z1234567890ABC  # Route53 hosted zone ID
```

**Modified File:** `infrastructure/pulumi/components/loadbalancer.ts`
```typescript
export interface LoadBalancerArgs {
    // ... existing fields ...
    domainName?: string;
    hostedZoneId?: string;
}

export class LoadBalancerComponent extends pulumi.ComponentResource {
    // ... existing code ...

    constructor(name: string, args: LoadBalancerArgs, opts?: pulumi.ComponentResourceOptions) {
        // ... existing code ...

        // Force HTTPS redirect for production
        this.httpListener = new aws.lb.Listener(`${name}-http-listener`, {
            loadBalancerArn: this.alb.arn,
            port: 80,
            protocol: "HTTP",
            defaultActions: [
                {
                    type: "redirect",
                    redirect: {
                        port: "443",
                        protocol: "HTTPS",
                        statusCode: "HTTP_301",
                    },
                },
            ],
            // ... rest of configuration ...
        });

        // Add Route53 DNS record if domain is configured
        if (args.domainName && args.hostedZoneId) {
            new aws.route53.Record(`${name}-dns-record`, {
                zoneId: args.hostedZoneId,
                name: args.domainName,
                type: "A",
                aliases: [
                    {
                        name: this.alb.dnsName,
                        zoneId: this.alb.zoneId,
                        evaluateTargetHealth: true,
                    },
                ],
            }, { parent: this });
        }

        // ... rest of existing code ...
    }
}
```

#### 2.3 Security Headers via ALB

**New File:** `infrastructure/pulumi/components/security-headers.ts`
```typescript
export function createSecurityHeadersRule(
    listener: aws.lb.Listener,
    targetGroup: aws.lb.TargetGroup,
    priority: number
): aws.lb.ListenerRule {
    return new aws.lb.ListenerRule("security-headers-rule", {
        listenerArn: listener.arn,
        priority: priority,
        actions: [
            {
                type: "forward",
                targetGroupArn: targetGroup.arn,
                fixedResponse: {
                    contentType: "text/plain",
                    statusCode: "200",
                    messageBody: "OK",
                },
            },
        ],
        conditions: [
            {
                pathPattern: {
                    values: ["/*"],
                },
            },
        ],
        // Response headers modification
        actions: [
            {
                type: "forward",
                targetGroupArn: targetGroup.arn,
                forward: {
                    targetGroups: [
                        {
                            arn: targetGroup.arn,
                            weight: 1,
                        },
                    ],
                },
            },
        ],
    });
}
```

### Phase 3: Application Security Enhancements

#### 3.1 Enhanced Middleware

**New File:** `src/interfaces/api/v1/middleware/security_headers.py`
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable
from fastapi.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS header (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # CSP header
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        return response
```

#### 3.2 Environment-Specific Configuration

**New File:** `.env.production`
```env
# HTTPS Configuration
USE_HTTPS=true
ALLOWED_HOSTS=api.happyrobot.com,*.happyrobot.com
USE_FORWARDED_HEADERS=true
FORWARDED_ALLOW_IPS=10.0.0.0/16

# Security Settings
SECURE_COOKIES=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=strict
```

---

## Manual Configuration Steps

### For Local Development

1. **Generate Certificates:**
   ```bash
   chmod +x scripts/generate-certs.sh
   ./scripts/generate-certs.sh
   ```

2. **Update .gitignore:**
   ```
   # Certificates
   certs/
   *.pem
   *.key
   *.crt
   *.csr
   ```

3. **Trust Certificate (Optional):**
   - **Windows:** Double-click `certs/server.crt` → Install Certificate → Local Machine → Trusted Root
   - **Mac:** `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/server.crt`
   - **Linux:** Copy to `/usr/local/share/ca-certificates/` and run `sudo update-ca-certificates`

4. **Start Services:**
   ```bash
   docker-compose down
   docker-compose up --build
   ```

5. **Test HTTPS:**
   ```bash
   curl -k https://localhost/api/v1/health
   ```

### For AWS Deployment

1. **Prerequisites:**
   - Domain name registered and configured
   - Route53 hosted zone created
   - AWS account with appropriate permissions

2. **Certificate Setup:**
   - Request certificate in ACM (see Section 2.1)
   - Validate domain ownership
   - Note the certificate ARN

3. **Update Pulumi Config:**
   ```bash
   cd infrastructure/pulumi
   pulumi config set certificateArn arn:aws:acm:eu-south-2:xxxxx:certificate/xxxxx
   pulumi config set domainName api.happyrobot.com
   pulumi config set hostedZoneId Z1234567890ABC
   ```

4. **Deploy Infrastructure:**
   ```bash
   pulumi up
   ```

5. **Update HappyRobot Platform Webhooks:**
   - Change all webhook URLs from `http://` to `https://`
   - Update to use the new domain name instead of ALB DNS name
   - Test each webhook endpoint

### DNS Configuration

1. **For Custom Domain:**
   ```
   Type: A
   Name: api
   Value: ALIAS to ALB DNS name
   TTL: 300
   ```

2. **For Subdomain:**
   ```
   Type: CNAME
   Name: prod-api
   Value: <alb-dns-name>.eu-south-2.elb.amazonaws.com
   TTL: 300
   ```

---

## Testing and Validation

### Local Environment Tests

```bash
# Test HTTPS redirect
curl -I http://localhost
# Expected: 301 redirect to https://localhost

# Test HTTPS endpoint
curl -k https://localhost/api/v1/health
# Expected: {"status": "ok"}

# Test API authentication over HTTPS
curl -k -H "X-API-Key: dev-local-api-key" https://localhost/api/v1/loads/search \
  -H "Content-Type: application/json" \
  -d '{"origin_state": "CA"}'

# Check security headers
curl -k -I https://localhost/api/v1/health | grep -i strict-transport
```

### AWS Environment Tests

```bash
# Test certificate validation
openssl s_client -connect api.happyrobot.com:443 -servername api.happyrobot.com

# Test HTTPS redirect
curl -I http://api.happyrobot.com
# Expected: 301 redirect

# Test API endpoint
curl https://api.happyrobot.com/api/v1/health

# Load test with HTTPS
ab -n 1000 -c 10 -H "X-API-Key: your-api-key" https://api.happyrobot.com/api/v1/health
```

### Security Validation

```bash
# SSL Labs test (for production)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.happyrobot.com

# Security headers test
# Visit: https://securityheaders.com/?q=api.happyrobot.com

# OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://api.happyrobot.com
```

---

## Rollback Plan

### Local Environment Rollback

1. **Remove Nginx service from docker-compose.yml**
2. **Restore original ports configuration**
3. **Delete certificates directory**
4. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up --build
   ```

### AWS Environment Rollback

1. **Pulumi Rollback:**
   ```bash
   cd infrastructure/pulumi
   pulumi stack history
   pulumi stack select happyrobot-prod
   pulumi up --target-dependents --target "<previous-state-urn>"
   ```

2. **Manual ALB Rollback:**
   - Remove HTTPS listener from ALB
   - Update HTTP listener to forward instead of redirect
   - Remove certificate association

3. **Update webhook URLs back to HTTP**

---

## Security Best Practices Implemented

1. **TLS Configuration:**
   - TLS 1.2 minimum, TLS 1.3 preferred
   - Strong cipher suites only
   - Perfect Forward Secrecy enabled

2. **Security Headers:**
   - HSTS with preload
   - CSP policy configured
   - X-Frame-Options to prevent clickjacking
   - X-Content-Type-Options to prevent MIME sniffing

3. **Certificate Management:**
   - Automated renewal via ACM in AWS
   - 2048-bit RSA keys minimum
   - Certificate transparency logging

4. **Network Security:**
   - HTTPS-only communication enforced
   - Security groups properly configured
   - WAF protection in production

---

## Monitoring and Alerts

### Metrics to Monitor

1. **Certificate Expiry:**
   - ACM certificate days until expiry
   - Alert threshold: 30 days

2. **SSL/TLS Errors:**
   - SSL handshake failures
   - Certificate validation errors
   - Protocol downgrade attempts

3. **Performance Impact:**
   - HTTPS latency vs HTTP baseline
   - SSL termination CPU usage
   - Connection establishment time

### CloudWatch Alarms

```typescript
// Add to monitoring component
new aws.cloudwatch.MetricAlarm("cert-expiry-alarm", {
    alarmName: "happyrobot-cert-expiry",
    comparisonOperator: "LessThanThreshold",
    evaluationPeriods: 1,
    metricName: "DaysToExpiry",
    namespace: "AWS/CertificateManager",
    period: 86400,
    statistic: "Average",
    threshold: 30,
    alarmDescription: "Alert when certificate expires in 30 days",
});
```

---

## Cost Implications

### Estimated Monthly Costs

| Service | Cost | Notes |
|---------|------|-------|
| ACM Certificate | $0 | Free for AWS resources |
| Additional ALB Rules | ~$0.50 | For HTTPS listener rules |
| Data Transfer (HTTPS overhead) | ~$5-10 | ~3% overhead on existing traffic |
| CloudWatch Metrics | ~$2 | Additional monitoring |
| **Total Additional Cost** | **~$8-13/month** | Minimal impact |

---

## Timeline and Milestones

| Phase | Duration | Dependencies | Deliverables |
|-------|----------|--------------|--------------|
| Local HTTPS Setup | 2 hours | None | Self-signed certs, Nginx proxy |
| FastAPI Updates | 1 hour | Local HTTPS | Security middleware, config |
| AWS Certificate | 1 hour | Domain access | ACM certificate validated |
| Infrastructure Updates | 1 hour | Certificate ARN | Pulumi deployment |
| Testing & Validation | 1 hour | All above | Test results, security scan |
| Documentation | 30 mins | All above | Updated README, runbooks |

---

## Appendix

### A. Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Certificate validation fails | Check DNS records, wait for propagation |
| Mixed content warnings | Update all internal URLs to use HTTPS |
| Performance degradation | Enable HTTP/2, optimize cipher suites |
| Certificate renewal fails | Check Route53 permissions, DNS validation |

### B. Useful Commands

```bash
# Check certificate expiry
echo | openssl s_client -servername api.happyrobot.com -connect api.happyrobot.com:443 2>/dev/null | openssl x509 -noout -dates

# Test TLS versions
nmap --script ssl-enum-ciphers -p 443 api.happyrobot.com

# Monitor HTTPS traffic
tcpdump -i any -s 0 -A 'tcp port 443'
```

### C. References

- [FastAPI HTTPS Documentation](https://fastapi.tiangolo.com/deployment/https/)
- [AWS Certificate Manager Guide](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

---

## Approval and Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Development Lead | | | |
| Security Officer | | | |
| DevOps Engineer | | | |
| Product Owner | | | |

---

*Document Version: 1.0*
*Last Updated: 2025-01-20*
*Next Review Date: 2025-02-20*
