#!/bin/bash

# HappyRobot FDE - HTTPS Testing Script
# Tests both local and deployed HTTPS configurations
# Verifies security headers are properly set

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOCAL_HTTP_URL="http://localhost:8000"
LOCAL_HTTPS_URL="https://localhost:443"
DEPLOYED_URL="${DEPLOYED_URL:-https://api.happyrobot.com}"
API_KEY="${API_KEY:-dev-local-api-key}"

echo -e "${BLUE}=== HappyRobot FDE HTTPS Testing Script ===${NC}"
echo

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2
    echo -n "Checking if $name is running... "
    # Use -k flag to allow self-signed certificates
    if curl -s -k -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url/api/v1/health" | grep -q "200"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not accessible${NC}"
        return 1
    fi
}

# Function to test security headers
test_security_headers() {
    local url=$1
    local test_name=$2
    local endpoint=$3

    echo -e "\n${YELLOW}Testing Security Headers: $test_name${NC}"
    echo "URL: $url$endpoint"
    echo

    # Make request and capture headers
    local response_file=$(mktemp)
    local headers_file=$(mktemp)

    if curl -s -k -X GET -I -H "X-API-Key: $API_KEY" "$url$endpoint" > "$headers_file" 2>&1; then
        echo -e "${GREEN}✓ Request successful${NC}"

        # Check individual security headers
        local headers=(
            "X-Content-Type-Options:nosniff"
            "X-Frame-Options:DENY"
            "X-XSS-Protection:1; mode=block"
            "Referrer-Policy:strict-origin-when-cross-origin"
            "Content-Security-Policy:default-src"
            "Cross-Origin-Opener-Policy:same-origin"
            "Cross-Origin-Embedder-Policy:require-corp"
            "Cross-Origin-Resource-Policy:same-origin"
            "Server:HappyRobot-API"
            "X-Powered-By:HappyRobot-FDE"
        )

        for header in "${headers[@]}"; do
            local header_name=$(echo "$header" | cut -d: -f1)
            local expected_value=$(echo "$header" | cut -d: -f2)

            if grep -i "^$header_name:" "$headers_file" | grep -q "$expected_value"; then
                echo -e "  ${GREEN}✓ $header_name${NC}"
            else
                echo -e "  ${RED}✗ $header_name (missing or incorrect)${NC}"
            fi
        done

        # Check HSTS header (should only be present on HTTPS)
        if [[ "$url" == https* ]]; then
            if grep -i "^Strict-Transport-Security:" "$headers_file" > /dev/null; then
                echo -e "  ${GREEN}✓ Strict-Transport-Security (HTTPS)${NC}"
            else
                echo -e "  ${YELLOW}! Strict-Transport-Security (not found - check ENABLE_HTTPS setting)${NC}"
            fi
        else
            if grep -i "^Strict-Transport-Security:" "$headers_file" > /dev/null; then
                echo -e "  ${YELLOW}! Strict-Transport-Security (present on HTTP - should only be on HTTPS)${NC}"
            else
                echo -e "  ${GREEN}✓ Strict-Transport-Security (correctly absent on HTTP)${NC}"
            fi
        fi

        echo
        echo "Full headers response:"
        cat "$headers_file"

    else
        echo -e "${RED}✗ Request failed${NC}"
        cat "$headers_file"
    fi

    # Cleanup
    rm -f "$response_file" "$headers_file"
}

# Function to test API functionality
test_api_functionality() {
    local url=$1
    local test_name=$2

    echo -e "\n${YELLOW}Testing API Functionality: $test_name${NC}"
    echo "URL: $url"
    echo

    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -s -k "$url/api/v1/health" | grep -q '"status":"ok"'; then
        echo -e "${GREEN}✓ Health endpoint working${NC}"
    else
        echo -e "${RED}✗ Health endpoint failed${NC}"
    fi

    # Test authenticated endpoint
    echo "Testing authenticated endpoint..."
    local auth_response=$(curl -s -k -w "%{http_code}" -H "X-API-Key: $API_KEY" "$url/api/v1/loads/search" -H "Content-Type: application/json" -d '{"origin_city": "test", "destination_city": "test"}')
    local http_code="${auth_response: -3}"

    if [[ "$http_code" == "200" ]] || [[ "$http_code" == "422" ]]; then
        echo -e "${GREEN}✓ Authenticated endpoint accessible${NC}"
    else
        echo -e "${RED}✗ Authenticated endpoint failed (HTTP $http_code)${NC}"
    fi

    # Test unauthenticated request
    echo "Testing unauthenticated request..."
    local unauth_response=$(curl -s -k -w "%{http_code}" -o /dev/null "$url/api/v1/loads/search" -H "Content-Type: application/json" -d '{"origin_city": "test", "destination_city": "test"}')

    if [[ "$unauth_response" == "401" ]]; then
        echo -e "${GREEN}✓ Unauthenticated request properly rejected${NC}"
    else
        echo -e "${RED}✗ Unauthenticated request not properly handled (HTTP $unauth_response)${NC}"
    fi
}

# Function to test SSL certificate
test_ssl_certificate() {
    local url=$1
    local test_name=$2

    echo -e "\n${YELLOW}Testing SSL Certificate: $test_name${NC}"
    echo "URL: $url"
    echo

    # Extract hostname and port
    local hostname=$(echo "$url" | sed 's|https://||' | sed 's|:.*||')
    local port=$(echo "$url" | grep -o ':[0-9]*' | sed 's|:||' || echo "443")

    # Test SSL connection
    if openssl s_client -connect "$hostname:$port" -servername "$hostname" </dev/null 2>/dev/null | openssl x509 -noout -text 2>/dev/null; then
        echo -e "${GREEN}✓ SSL certificate accessible${NC}"

        # Get certificate info
        echo "Certificate information:"
        openssl s_client -connect "$hostname:$port" -servername "$hostname" </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates 2>/dev/null

    else
        echo -e "${YELLOW}! SSL certificate test failed (expected for self-signed certificates)${NC}"
    fi
}

# Main testing sequence
echo -e "${BLUE}Starting HTTPS tests...${NC}"
echo

# Test 1: Local HTTP (direct API)
if check_service "$LOCAL_HTTP_URL" "Local API (HTTP)"; then
    test_security_headers "$LOCAL_HTTP_URL" "Local HTTP API" "/api/v1/health"
    test_api_functionality "$LOCAL_HTTP_URL" "Local HTTP API"
fi

# Test 2: Local HTTPS (via nginx)
echo -e "\n${BLUE}--- Testing Local HTTPS Setup ---${NC}"
if check_service "$LOCAL_HTTPS_URL" "Local HTTPS (nginx)"; then
    test_ssl_certificate "$LOCAL_HTTPS_URL" "Local HTTPS"
    test_security_headers "$LOCAL_HTTPS_URL" "Local HTTPS" "/api/v1/health"
    test_api_functionality "$LOCAL_HTTPS_URL" "Local HTTPS"
else
    echo -e "${YELLOW}Local HTTPS not available. Make sure to run: docker-compose up${NC}"
fi

# Test 3: Deployed environment (if URL provided)
if [[ "$DEPLOYED_URL" != "https://api.happyrobot.com" ]]; then
    echo -e "\n${BLUE}--- Testing Deployed HTTPS Setup ---${NC}"
    if check_service "$DEPLOYED_URL" "Deployed API"; then
        test_ssl_certificate "$DEPLOYED_URL" "Deployed HTTPS"
        test_security_headers "$DEPLOYED_URL" "Deployed HTTPS" "/api/v1/health"
        test_api_functionality "$DEPLOYED_URL" "Deployed HTTPS"
    fi
else
    echo -e "\n${YELLOW}Skipping deployed tests. Set DEPLOYED_URL environment variable to test deployed instance.${NC}"
fi

# Test 4: HTTP to HTTPS redirect
echo -e "\n${BLUE}--- Testing HTTP to HTTPS Redirect ---${NC}"
if check_service "http://localhost" "Local HTTP (nginx)"; then
    echo "Testing HTTP to HTTPS redirect..."
    redirect_response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost/api/v1/health")

    if [[ "$redirect_response" == "301" ]]; then
        echo -e "${GREEN}✓ HTTP to HTTPS redirect working${NC}"
    else
        echo -e "${YELLOW}! HTTP redirect returned $redirect_response (may be allowed for health checks)${NC}"
    fi
fi

echo -e "\n${BLUE}=== HTTPS Testing Complete ===${NC}"
echo
echo -e "${YELLOW}Notes:${NC}"
echo "- Self-signed certificates will show warnings but should still work"
echo "- HSTS headers should only appear on HTTPS responses"
echo "- Some tests may fail if services are not running"
echo "- Set DEPLOYED_URL environment variable to test production deployments"
echo
echo -e "${YELLOW}Usage Examples:${NC}"
echo "  # Test local development setup"
echo "  ./scripts/test-https.sh"
echo
echo "  # Test deployed environment"
echo "  DEPLOYED_URL=https://your-api.domain.com ./scripts/test-https.sh"
echo
echo "  # Test with custom API key"
echo "  API_KEY=your-api-key ./scripts/test-https.sh"
