#!/bin/bash
# Run this on your EC2 instance after SSH-ing in.
# Usage: chmod +x setup_ec2.sh && ./setup_ec2.sh

set -e

echo "=== 1. System update ==="
sudo apt-get update -y && sudo apt-get upgrade -y

echo "=== 2. Install Docker ==="
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

echo "=== 3. Install nginx ==="
sudo apt-get install -y nginx

echo "=== 4. Install certbot ==="
sudo apt-get install -y certbot python3-certbot-nginx

echo "=== 5. Install git ==="
sudo apt-get install -y git

echo ""
echo "✓ Setup complete. Now:"
echo "  1. Log out and back in (so Docker group takes effect)"
echo "  2. Clone your repo:  git clone https://github.com/YOUR_USERNAME/instagram-agent.git"
echo "  3. cd instagram-agent && cp .env.example .env && nano .env"
echo "  4. Run:  docker compose -f docker-compose.prod.yml up -d --build"
echo "  5. Configure nginx (see deploy/README.md)"
