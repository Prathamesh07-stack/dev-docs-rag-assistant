# Quick Start: Deploy to Cloudflare

This is a quick reference. See [CLOUDFLARE_DEPLOYMENT_GUIDE.md](CLOUDFLARE_DEPLOYMENT_GUIDE.md) for detailed instructions.

## 1️⃣ Choose Your Backend Platform

### Option A: Railway (Recommended - 5 minutes)
```bash
# 1. Push to GitHub
git push origin main

# 2. Go to https://railway.app
# 3. Sign in with GitHub
# 4. Select your repo and deploy (auto-detects railway.json)
# 5. Copy the backend URL
```

### Option B: Render (5 minutes)
```bash
# 1. Go to https://render.com
# 2. Sign in with GitHub  
# 3. Create new Web Service
# 4. Select your repo
# 5. It auto-detects render.yaml and deploys
```

### Option C: Self-Hosted VPS (15 minutes)
```bash
# On your VPS:
git clone your-repo
cd rag-chatbot
docker-compose -f infra/docker-compose.yml up -d
```

---

## 2️⃣ Deploy Frontend to Cloudflare Pages

```bash
# 1. Create GitHub repo (if not already done)
git push origin main

# 2. Go to Cloudflare Dashboard → Pages
# 3. Click "Create a project" → "Connect to Git"
# 4. Select your repository
# 5. Build Settings:
#    - Framework: Next.js
#    - Build command: npm run build
#    - Build output: out
#    - Root directory: frontend
# 6. Add Environment Variables:
#    NEXT_PUBLIC_API_URL=<your-backend-url>
# 7. Click "Save and Deploy"
```

---

## 3️⃣ Update CORS on Backend

```bash
# Set this environment variable on your backend:
ALLOWED_ORIGINS=https://your-project.pages.dev,https://yourdomain.com
```

---

## 4️⃣ Test

```bash
# Test frontend
open https://your-project.pages.dev

# Test API
curl https://your-backend-url/health
```

---

## 📋 Environment Variables Needed

### Frontend (Cloudflare Pages)
```
NEXT_PUBLIC_API_URL=https://your-backend-url
NODE_ENV=production
```

### Backend (Railway/Render/VPS)
```
ENV=production
ALLOWED_ORIGINS=https://your-project.pages.dev
DATA_DIR=/app/data
CONFIG_PATH=/app/config/sources.yaml
```

---

## 🔗 Useful Links

- **Cloudflare Pages Documentation**: https://developers.cloudflare.com/pages/
- **Railway Documentation**: https://docs.railway.app/
- **Render Documentation**: https://docs.render.com/
- **Next.js Deployment**: https://nextjs.org/docs/deployment

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Check `ALLOWED_ORIGINS` includes Cloudflare domain |
| 502 Bad Gateway | Check backend is running; view logs |
| Build fails | Ensure `frontend` is root dir; check npm install |
| API not responding | Verify `NEXT_PUBLIC_API_URL` is correct |

---

**See [CLOUDFLARE_DEPLOYMENT_GUIDE.md](CLOUDFLARE_DEPLOYMENT_GUIDE.md) for detailed troubleshooting and production setup.**
