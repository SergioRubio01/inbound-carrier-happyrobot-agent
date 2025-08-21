# HTTPS Setup for Local Development

This document describes the HTTPS implementation for local development of the HappyRobot FDE API.

## Overview

The implementation adds Nginx as a reverse proxy to provide HTTPS termination with self-signed certificates for local development. This setup maintains all existing functionality while adding secure HTTPS access.

## Components

### 1. Nginx Reverse Proxy
- **Container**: `happyrobot-nginx` (nginx:1.25-alpine)
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Configuration**: `nginx/nginx.conf`

### 2. SSL Certificates
- **Location**: `certs/` directory (gitignored)
- **Type**: Self-signed certificates for development
- **Domains**: localhost, *.localhost, happyrobot-api, api.local
- **Generation**: Automated script `scripts/generate-certs.sh`

### 3. Security Features

#### Security Headers
- Strict-Transport-Security (HSTS)
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy (comprehensive)

#### Rate Limiting
- API endpoints: 100 requests/minute
- Health endpoints: 200 requests/minute
- Burst handling with graceful queuing

## Access Points

### HTTP (Port 80)
- Health endpoints: Direct access allowed
- All other traffic: Redirected to HTTPS (301)

### HTTPS (Port 443)
- Full API access with authentication
- API documentation at `/api/v1/docs`
- OpenAPI spec at `/api/v1/openapi.json`
- Root path redirects to documentation

## Usage

### Starting Services
```bash
# Generate certificates (first time only)
bash scripts/generate-certs.sh

# Start all services
docker compose up --build
```

### Access URLs
- **API Documentation**: https://localhost/api/v1/docs
- **API Health**: https://localhost/api/v1/health
- **API Endpoints**: https://localhost/api/v1/*

### Browser Access
1. Navigate to https://localhost
2. Accept security warning (self-signed certificate)
3. Proceed to API documentation

## Development Notes

- The FastAPI application remains unchanged
- API key authentication still required for protected endpoints
- All existing Docker health checks continue to work
- Backward compatibility maintained for internal service communication

## Files Modified/Created

- `nginx/nginx.conf` - Nginx configuration
- `docker-compose.yml` - Added nginx service
- `scripts/generate-certs.sh` - Certificate generation script
- `.gitignore` - Added certificate exclusions
- `certs/` - Certificate directory (gitignored)

## Security Considerations

- Self-signed certificates are for development only
- Do not use these certificates in production
- Certificates include multiple SANs for flexibility
- Private keys are properly protected (600 permissions)
