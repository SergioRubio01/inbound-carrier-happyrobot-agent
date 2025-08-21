#!/bin/bash

# Generate self-signed certificates for local HTTPS development
# This script creates SSL certificates for the HappyRobot API

set -e

# Configuration
CERT_DIR="certs"
DOMAIN="localhost"
DAYS=365
KEY_SIZE=2048

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 HappyRobot Certificate Generator${NC}"
echo "Generating self-signed SSL certificates for local development..."
echo

# Create certificates directory if it doesn't exist
if [ ! -d "$CERT_DIR" ]; then
    echo -e "${YELLOW}📁 Creating certificates directory: $CERT_DIR${NC}"
    mkdir -p "$CERT_DIR"
fi

# Check if certificates already exist
if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ]; then
    echo -e "${YELLOW}⚠️  Certificates already exist!${NC}"
    read -p "Do you want to regenerate them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ Using existing certificates${NC}"
        exit 0
    fi
    echo -e "${YELLOW}🔄 Regenerating certificates...${NC}"
fi

# Generate private key
echo -e "${YELLOW}🔑 Generating private key...${NC}"
openssl genrsa -out "$CERT_DIR/server.key" $KEY_SIZE

# Generate certificate signing request
echo -e "${YELLOW}📝 Creating certificate signing request...${NC}"
openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" -subj "//C=US\ST=Development\L=Local\O=HappyRobot\OU=Development\CN=$DOMAIN"

# Generate self-signed certificate with SAN extension
echo -e "${YELLOW}📜 Generating self-signed certificate...${NC}"
cat > "$CERT_DIR/cert.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Development
L = Local
O = HappyRobot
OU = Development
CN = $DOMAIN

[v3_req]
keyUsage = digitalSignature, keyEncipherment, dataEncipherment, keyAgreement
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = happyrobot-api
DNS.4 = api.local
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

openssl x509 -req -in "$CERT_DIR/server.csr" -signkey "$CERT_DIR/server.key" -out "$CERT_DIR/server.crt" -days $DAYS -extensions v3_req -extfile "$CERT_DIR/cert.conf"

# Set appropriate permissions
echo -e "${YELLOW}🔒 Setting file permissions...${NC}"
chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

# Clean up temporary files
rm -f "$CERT_DIR/server.csr" "$CERT_DIR/cert.conf"

# Display certificate information
echo -e "${GREEN}✅ Certificates generated successfully!${NC}"
echo
echo -e "${YELLOW}📋 Certificate Details:${NC}"
echo "  📁 Location: $CERT_DIR/"
echo "  🔑 Private Key: server.key"
echo "  📜 Certificate: server.crt"
echo "  🌐 Domain: $DOMAIN"
echo "  📅 Valid for: $DAYS days"
echo
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo "  1. Run: docker compose up --build"
echo "  2. Access API at: https://localhost"
echo "  3. Accept the security warning in your browser (self-signed certificate)"
echo
echo -e "${RED}⚠️  Security Notice:${NC}"
echo "  These are self-signed certificates for development only!"
echo "  Do NOT use these certificates in production!"
echo
echo -e "${GREEN}🎉 Happy coding with HTTPS!${NC}"
