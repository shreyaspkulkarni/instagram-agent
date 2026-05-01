# Deployment Guide

Stack: EC2 t2.micro (backend) + Vercel (frontend)

---

## Step 1 — Push to GitHub

```bash
# In the project root
git init
git add .
git commit -m "initial commit"
```

Create a new repo on github.com (don't add README/gitignore), then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/instagram-agent.git
git push -u origin main
```

---

## Step 2 — Launch EC2

1. Go to **EC2 → Launch Instance**
2. Choose: **Ubuntu 22.04 LTS**, **t2.micro** (free tier)
3. Create a key pair → download the `.pem` file
4. Security group — add inbound rules:
   - SSH: port 22, source My IP
   - HTTP: port 80, source Anywhere
   - HTTPS: port 443, source Anywhere
5. Launch

---

## Step 3 — Elastic IP + Domain

1. EC2 → **Elastic IPs → Allocate**, then associate with your instance
2. In your domain registrar (Namecheap, etc.), add an **A record**:
   - Host: `api` (gives you `api.yourdomain.com`)
   - Value: your Elastic IP
3. Wait ~5 minutes for DNS to propagate

---

## Step 4 — Server Setup

```bash
# Copy setup script to EC2
scp -i your-key.pem deploy/setup_ec2.sh ubuntu@YOUR_ELASTIC_IP:~

# SSH in
ssh -i your-key.pem ubuntu@YOUR_ELASTIC_IP

# Run setup (installs Docker, nginx, certbot, git)
chmod +x setup_ec2.sh && ./setup_ec2.sh

# Log out and back in so Docker group takes effect
exit
ssh -i your-key.pem ubuntu@YOUR_ELASTIC_IP
```

---

## Step 5 — Deploy Backend

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/instagram-agent.git
cd instagram-agent

# Set up environment
cp .env.example .env
nano .env  # fill in ANTHROPIC_API_KEY, GOOGLE_API_KEY, POSTGRES_PASSWORD, SECRET_KEY

# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build

# Check everything is running
docker compose -f docker-compose.prod.yml ps

# Seed the RAG data (one-time)
docker compose -f docker-compose.prod.yml exec api python data/ingest_rag.py
```

---

## Step 6 — Configure HTTPS with nginx

```bash
# Copy nginx config
sudo cp deploy/nginx.conf /etc/nginx/sites-available/instagram-agent

# Replace YOUR_DOMAIN with your actual domain (e.g. api.yourdomain.com)
sudo sed -i 's/YOUR_DOMAIN/api.yourdomain.com/g' /etc/nginx/sites-available/instagram-agent

# Enable the site
sudo ln -s /etc/nginx/sites-available/instagram-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Get SSL certificate (replace with your domain and email)
sudo certbot --nginx -d api.yourdomain.com --email you@email.com --agree-tos --non-interactive

# Reload nginx
sudo systemctl reload nginx
```

Test it: `curl https://api.yourdomain.com/health` → should return `{"status":"ok"}`

---

## Step 7 — Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project** → Import from GitHub
2. Select your `instagram-agent` repo
3. Set **Root Directory** to `frontend`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://api.yourdomain.com`
5. Click **Deploy**

---

## Updating the deployment

```bash
# On EC2
cd ~/instagram-agent
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Vercel redeploys automatically on every push to `main`.

---

## Costs (AWS free tier, 12 months)

| Resource | Free tier | After 12 months |
|---|---|---|
| EC2 t2.micro | 750 hrs/month free | ~$8.50/month |
| Elastic IP | Free while attached | Free while attached |
| Data transfer | 100GB/month free | $0.09/GB |
| Vercel | Free forever | Free forever |
| Domain | ~$10/year | ~$10/year |
