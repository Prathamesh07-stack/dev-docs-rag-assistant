# Cloudflare Deployment Guide for RAG Chatbot

## Overview
This guide covers deploying your RAG chatbot across multiple platforms:
- **Frontend (Next.js)**: Cloudflare Pages
- **Backend (FastAPI)**: Railway, Render, or self-hosted VPS
- **Vector Database (Chroma)**: Hosted with backend

---

## PHASE 1: Prepare Your Project

### Step 1.1: Update CORS Settings in Backend
The backend CORS is currently hardcoded to localhost. Update it to accept your Cloudflare Pages domain.

**File**: `backend/main.py`

```python
# Update the CORS allowed origins
allow_origins=[
    "http://localhost:3000",      # Local dev
    "http://127.0.0.1:3000",      # Local dev
    "https://*.pages.dev",        # Cloudflare Pages
    "https://yourdomain.com",     # Your custom domain (if using one)
]
```

### Step 1.2: Configure Environment Variables
Create `.env.production` files for both frontend and backend.

**Backend** (`backend/.env.production`):
```bash
ENV=production
DATABASE_URL=sqlite:////app/data/rag.db
CHROMA_HOST=localhost
CHROMA_PORT=8000
DATA_DIR=/app/data
CONFIG_PATH=/app/config/sources.yaml
LOG_LEVEL=info
```

**Frontend** (`frontend/.env.production.local`):
```bash
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

### Step 1.3: Update next.config.ts for Cloudflare
Since you already have `@cloudflare/next-on-pages` in devDependencies, update your Next.js config:

```typescript
// frontend/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Improve build time
  swcMinify: true,
  
  // Optimize for serverless
  output: "standalone",
  
  // Ensure function routes work on Cloudflare
  /* config options here */
};

export default nextConfig;
```

### Step 1.4: Create wrangler.toml for Cloudflare Pages
Create this file in your frontend directory for Cloudflare configuration:

**File**: `frontend/wrangler.toml`

```toml
#:schema node_modules/wrangler/config-schema.json
name = "rag-chatbot-frontend"
type = "javascript"
account_id = ""  # Add your Cloudflare account ID
workers_dev = true
main = "src/index.ts"
compatibility_date = "2024-12-16"

routes = [
  { pattern = "example.com", zone_name = "example.com" }
]

env = {
  production = {
    routes = [
      { pattern = "yourdomain.com", zone_name = "yourdomain.com" }
    ]
  }
}
```

---

## PHASE 2: Deploy Frontend to Cloudflare Pages

### Step 2.1: Prepare for Cloudflare Pages
```bash
cd frontend

# Install Cloudflare Pages adapter
npm install --save-dev @cloudflare/next-on-pages

# For experimental support
npm install --save-dev wrangler
```

### Step 2.2: Build Locally (Optional Test)
```bash
npm run build
```

### Step 2.3: Create GitHub Repository (Required for Cloudflare Pages)
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit for Cloudflare deployment"

# Add remote and push to GitHub
git remote add origin https://github.com/your-username/rag-chatbot.git
git branch -M main
git push -u origin main
```

### Step 2.4: Connect to Cloudflare Pages
1. **Go to Cloudflare Dashboard** → Pages
2. **Click "Create a project"** → "Connect to Git"
3. **Select your repository** (rag-chatbot)
4. **Configure build settings**:
   - Framework preset: `Next.js`
   - Build command: `npm run build`
   - Build output directory: `out` or `.next`
   - Root directory: `frontend`
5. **Add Environment Variables**:
   - `NEXT_PUBLIC_API_URL=https://your-backend-url.com`
   - `NODE_ENV=production`
6. **Click "Save and Deploy"**

### Step 2.5: Connect Custom Domain (Optional)
1. Go to your Pages project → Settings → Custom domains
2. Add your domain (e.g., `chatbot.yourdomain.com`)
3. Update your DNS to point to Cloudflare

---

## PHASE 3: Deploy Backend

### Option A: Deploy to Railway (Recommended - Easiest)

#### Step 3A.1: Prepare Your Backend
```bash
cd backend

# Create railway.json
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT"
  }
}
EOF
```

#### Step 3A.2: Push to GitHub
```bash
git add backend/railway.json
git commit -m "Add Railway deployment config"
git push origin main
```

#### Step 3A.3: Deploy on Railway
1. **Go to [railway.app](https://railway.app)**
2. **Sign in with GitHub**
3. **Create new project** → "Deploy from GitHub repo"
4. **Select your rag-chatbot repository**
5. **Add variables** in Railway dashboard:
   ```
   ENV=production
   DATA_DIR=/app/data
   CONFIG_PATH=/app/config/sources.yaml
   PORT=8000
   ```
6. **Railway automatically deploys** from your Dockerfile

#### Step 3A.4: Get Your Backend URL
- Railway provides a URL like: `https://rag-backend-prod.up.railway.app`
- Update your frontend's `NEXT_PUBLIC_API_URL` with this URL

---

### Option B: Deploy to Render.com

#### Step 3B.1: Create render.yaml
**File**: `backend/render.yaml`

```yaml
services:
  - type: web
    name: rag-chatbot-backend
    runtime: python
    pythonVersion: 3.11
    buildCommand: "pip install --upgrade pip && pip install -r requirements.txt"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: ENV
        value: production
      - key: DATA_DIR
        value: /app/data
      - key: CONFIG_PATH
        value: /app/config/sources.yaml
```

#### Step 3B.2: Deploy
1. Go to [render.com](https://render.com)
2. Click "Create +" → "Web Service"
3. Connect your GitHub repository
4. Render automatically detects `render.yaml`
5. Review settings and deploy

---

### Option C: Self-Host on VPS (AWS EC2, DigitalOcean, Linode)

#### Step 3C.1: Provision Server
```bash
# SSH into your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y
```

#### Step 3C.2: Set Up Application
```bash
# Clone your repository
git clone https://github.com/your-username/rag-chatbot.git
cd rag-chatbot

# Create .env file
cat > .env << 'EOF'
ENV=production
DATA_DIR=/app/data
CONFIG_PATH=/app/config/sources.yaml
EOF

# Update docker-compose.yml for production
# (See Step 3C.3 below)
```

#### Step 3C.3: Update docker-compose.yml for Production
Edit `infra/docker-compose.yml`:

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: rag-backend
    ports:
      - "127.0.0.1:8000:8000"  # Only expose to localhost
    volumes:
      - ../data:/app/data
      - ../config:/app/config
    environment:
      - ENV=production
      - DATA_DIR=/app/data
      - CONFIG_PATH=/app/config/sources.yaml
    depends_on:
      - chroma
    networks:
      - rag-network
    restart: always

  chroma:
    image: chromadb/chroma:latest
    container_name: rag-chroma
    ports:
      - "127.0.0.1:8001:8000"
    volumes:
      - chroma-data:/chroma/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
    networks:
      - rag-network
    restart: always

  nginx:
    image: nginx:latest
    container_name: rag-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    networks:
      - rag-network
    restart: always

volumes:
  chroma-data:

networks:
  rag-network:
```

#### Step 3C.4: Set Up Nginx Reverse Proxy
Create `infra/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;

    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        client_max_body_size 100M;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
        }
    }
}
```

#### Step 3C.5: Start Services
```bash
cd infra
docker-compose up -d

# View logs
docker-compose logs -f backend
```

---

## PHASE 4: Configure CORS and Environment Variables

### Step 4.1: Update Backend CORS
Edit `backend/main.py`:

```python
# Get allowed origins from environment
import os

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 4.2: Set Environment Variables in Deployment

**For Railway/Render**: Add these in their dashboard:
```
ALLOWED_ORIGINS=https://your-frontend.pages.dev,https://yourdomain.com
```

**For Self-Hosted**: Update `.env`:
```bash
ALLOWED_ORIGINS=https://your-frontend.pages.dev,https://yourdomain.com
```

---

## PHASE 5: Set Up Custom Domain (Optional)

### Step 5.1: Point Domain to Cloudflare Pages
1. Update domain DNS to use Cloudflare nameservers
2. In Cloudflare dashboard, add your domain
3. Go to Pages → Your project → Custom domains
4. Add your domain (e.g., `chatbot.yourdomain.com`)

### Step 5.2: Set Backend Domain
- Use Cloudflare to proxy API calls if needed, or
- Use the direct backend URL (Railway/Render/VPS)

---

## PHASE 6: Testing & Monitoring

### Step 6.1: Test Frontend
```bash
# Visit your Cloudflare Pages URL
https://your-project.pages.dev
```

### Step 6.2: Test API Call
```bash
# Test health endpoint
curl https://your-backend-url.com/health

# Should return:
# {"status":"ok","version":"0.1.0"}
```

### Step 6.3: Monitor Logs
- **Cloudflare Pages**: Pages dashboard → Analytics
- **Railway**: Dashboard → Logs
- **Render**: Services → Logs
- **Self-hosted**: `docker-compose logs -f`

---

## PHASE 7: CI/CD Pipeline (Optional)

### Step 7.1: Automatic Deployments
Both Cloudflare Pages and Railway/Render support automatic deployments on git push:
- Push to `main` → Automatic build & deploy
- No additional configuration needed

### Step 7.2: Environment-Specific Builds
For staging:
```bash
git checkout -b staging
# Make changes
git push origin staging
```

Then configure separate deployment in Cloudflare/Railway for the `staging` branch.

---

## Troubleshooting

### Issue: CORS Errors
**Solution**: Verify `ALLOWED_ORIGINS` includes your Cloudflare domain
```bash
curl -H "Origin: https://your-project.pages.dev" \
     https://your-backend-url.com/health -v
```

### Issue: 502 Bad Gateway
**Solution**: Check backend logs
```bash
# Railway/Render: Check dashboard logs
# Self-hosted: docker-compose logs backend
```

### Issue: Vector Database Connection Failed
**Solution**: Ensure Chroma is running and accessible
```bash
# Test connection
curl http://backend:8001/api/v1/heartbeat
```

### Issue: Build Failures on Cloudflare Pages
**Solution**: 
1. Check build logs in Pages dashboard
2. Ensure `frontend` directory is root directory
3. Verify `npm install` completes successfully

---

## Production Checklist

- [ ] CORS configured for production domain
- [ ] Environment variables set in all platforms
- [ ] SSL/TLS certificate installed (auto via Cloudflare)
- [ ] Database backups configured
- [ ] Error logging set up (Sentry/LogRocket)
- [ ] Rate limiting enabled on API
- [ ] Security headers configured
- [ ] Monitoring & alerts set up
- [ ] API tests running via CI/CD
- [ ] Frontend performance optimized

---

## Next Steps

1. Choose your backend platform (Railway recommended)
2. Follow the appropriate deployment phase
3. Test the complete flow (frontend → backend → vector DB)
4. Set up monitoring & alerts
5. Configure custom domain if needed

