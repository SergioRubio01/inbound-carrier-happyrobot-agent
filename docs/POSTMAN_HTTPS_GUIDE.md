# Postman Configuration Guide for HappyRobot FDE HTTPS

## Overview
This guide helps you configure Postman to work with the HappyRobot FDE API's HTTPS setup, including handling self-signed certificates for local development.

## Quick Setup

### 1. Disable SSL Certificate Verification (Recommended for Local Development)

Since we're using self-signed certificates for local development, you need to disable SSL certificate verification in Postman:

1. **Open Postman Settings**:
   - Click the gear icon (⚙️) in the top right corner
   - Or go to `File → Settings` (Windows/Linux) or `Postman → Settings` (Mac)

2. **Disable SSL Verification**:
   - Navigate to the **Settings** tab
   - Find **SSL certificate verification**
   - Turn it **OFF**

3. **Optional - Disable Warning**:
   - Below SSL verification, find **"SSL certificate verification" warning**
   - Turn it **OFF** to stop seeing warnings about disabled verification

### 2. Configure Your Requests

#### Base URLs
- **Local HTTPS (via nginx)**: `https://localhost`
- **Local HTTP (direct API)**: `http://localhost:8000`
- **Production**: Will be your ALB endpoint when deployed

#### Authentication
Add the API key header to all requests:
- **Header Name**: `X-API-Key`
- **Header Value**: `dev-local-api-key` (or your configured API key)

### 3. Example Requests

#### Health Check (No Auth Required)
```
GET https://localhost/api/v1/health
```

#### Load Search (Auth Required)
```
POST https://localhost/api/v1/loads/search
Headers:
  X-API-Key: dev-local-api-key
  Content-Type: application/json

Body (JSON):
{
  "origin_city": "Chicago",
  "destination_city": "New York",
  "equipment_type": "Dry Van",
  "max_weight_lbs": 45000
}
```

#### Price Negotiation
```
POST https://localhost/api/v1/negotiations/evaluate
Headers:
  X-API-Key: dev-local-api-key
  Content-Type: application/json

Body (JSON):
{
  "load_id": "LOAD123",
  "carrier_mc": "123456",
  "proposed_rate": 2500.00,
  "negotiation_round": 1,
  "previous_offers": []
}
```

## Alternative: Import the Certificate (Optional)

If you prefer to keep SSL verification enabled, you can import the self-signed certificate:

### Method 1: Add Certificate to Postman

1. **Export the certificate**:
   ```bash
   openssl x509 -in certs/server.crt -out certs/server.pem -outform PEM
   ```

2. **In Postman Settings**:
   - Go to **Settings → Certificates**
   - Click **Add Certificate**
   - Set:
     - **Host**: `localhost`
     - **Port**: `443`
     - **CRT file**: Browse to `certs/server.pem`
     - **KEY file**: Browse to `certs/server.key` (if client auth is needed)

### Method 2: Add to System Trust Store

**Windows**:
1. Double-click `certs/server.crt`
2. Click **Install Certificate**
3. Select **Local Machine**
4. Choose **Place all certificates in the following store**
5. Select **Trusted Root Certification Authorities**
6. Complete the wizard and restart Postman

**macOS**:
1. Open Keychain Access
2. Drag `certs/server.crt` to **System** keychain
3. Double-click the certificate
4. Under **Trust**, set **When using this certificate** to **Always Trust**
5. Restart Postman

**Linux**:
```bash
sudo cp certs/server.crt /usr/local/share/ca-certificates/happyrobot.crt
sudo update-ca-certificates
```

## Creating a Postman Collection

### 1. Environment Variables

Create an environment with these variables:
```json
{
  "base_url": "https://localhost",
  "api_key": "dev-local-api-key"
}
```

### 2. Collection Pre-request Script

Add to collection settings to automatically include auth:
```javascript
pm.request.headers.add({
    key: 'X-API-Key',
    value: pm.environment.get('api_key')
});
```

### 3. Sample Collection Structure
```
HappyRobot FDE API
├── Health
│   └── GET {{base_url}}/api/v1/health
├── Loads
│   ├── POST {{base_url}}/api/v1/loads/search
│   └── GET {{base_url}}/api/v1/loads/{id}
├── Negotiations
│   └── POST {{base_url}}/api/v1/negotiations/evaluate
├── Calls
│   ├── POST {{base_url}}/api/v1/calls/handoff
│   └── POST {{base_url}}/api/v1/calls/finalize
└── Metrics
    └── GET {{base_url}}/api/v1/metrics/summary
```

## Troubleshooting

### Error: SSL Certificate Verification Failed
**Solution**: Disable SSL certificate verification in Postman settings (see Quick Setup)

### Error: KEY_USAGE_BIT_INCORRECT
**Solution**: The certificates have been regenerated with proper key usage. Restart Docker containers:
```bash
docker-compose restart nginx
```

### Error: Connection Refused
**Solution**: Ensure Docker containers are running:
```bash
docker-compose up -d
```

### Error: 401 Unauthorized
**Solution**: Add the `X-API-Key` header with value `dev-local-api-key`

### Error: CORS Issues
**Solution**: CORS is configured to allow all origins in development. If issues persist, check browser console.

## Security Headers Verification

When using HTTPS via nginx, you should see these security headers in Postman's response:
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `X-XSS-Protection`
- `Content-Security-Policy`
- `Referrer-Policy`

## Testing Workflow

1. **Start services**:
   ```bash
   docker-compose up -d
   ```

2. **Test health endpoint**:
   ```
   GET https://localhost/api/v1/health
   ```
   Expected: `{"status":"ok"}`

3. **Test authenticated endpoint**:
   ```
   GET https://localhost/api/v1/metrics/summary
   Headers: X-API-Key: dev-local-api-key
   ```

4. **Test API docs**:
   - Open browser: https://localhost/api/v1/docs
   - Accept the certificate warning
   - Interactive API documentation should load

## Production Considerations

When moving to production with a real SSL certificate:
1. Re-enable SSL certificate verification in Postman
2. Update the base URL to your production endpoint
3. Use production API keys
4. Remove any certificate exceptions added for local development

## Additional Resources

- [Postman SSL Certificates Documentation](https://learning.postman.com/docs/sending-requests/certificates/)
- [HappyRobot API Documentation](https://localhost/api/v1/docs)
- [HTTPS Implementation Guide](./HTTPS_DEPLOYMENT_GUIDE.md)
