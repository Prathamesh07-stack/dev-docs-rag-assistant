# ☁️ Cloudflare Deployment Checklist

Use this checklist as you deploy your RAG chatbot. Check off each item as you complete it.

---

## 📋 Pre-Deployment Setup

### Repository & Basic Setup
- [ ] Code pushed to GitHub (main branch)
- [ ] `.env.example` created with all environment variables
- [ ] `.gitignore` includes `.env`, `node_modules/`, `__pycache__/`, `*.pyc`
- [ ] README.md has clear setup instructions

### Backend Preparation
- [ ] `backend/main.py` updated to use `ALLOWED_ORIGINS` environment variable
- [ ] `backend/requirements.txt` verified and up-to-date
- [ ] `backend/Dockerfile` exists and tested locally
- [ ] `backend/railway.json` OR `backend/render.yaml` created (depending on choice)

### Frontend Preparation  
- [ ] `frontend/next.config.ts` optimized for serverless
- [ ] `frontend/package.json` includes `@cloudflare/next-on-pages`
- [ ] `frontend/.env.example` created with `NEXT_PUBLIC_API_URL`
- [ ] `frontend/wrangler.toml` created
- [ ] Build tested locally: `npm run build`

### Infrastructure Files
- [ ] `infra/nginx.conf` created (for self-hosted option)
- [ ] `CLOUDFLARE_DEPLOYMENT_GUIDE.md` reviewed
- [ ] `DEPLOYMENT_QUICK_START.md` bookmarked

---

## 🚀 Backend Deployment

### Choose One Path:

#### ✅ Path A: Railway (Recommended)
- [ ] Created account at https://railway.app
- [ ] Signed in with GitHub
- [ ] Set environment variables in Railway dashboard:
  - [ ] `ENV=production`
  - [ ] `DATA_DIR=/app/data`
  - [ ] `CONFIG_PATH=/app/config/sources.yaml`
  - [ ] `ALLOWED_ORIGINS=https://your-app.pages.dev`
- [ ] Deployment triggered automatically
- [ ] Copied backend URL: `https://rag-backend-prod.up.railway.app`
- [ ] Tested health endpoint: `curl https://your-backend-url/health`

**Status**: _______________

#### ✅ Path B: Render
- [ ] Created account at https://render.com
- [ ] Signed in with GitHub
- [ ] Selected repository and build settings auto-detected
- [ ] Verified environment variables in Render dashboard
- [ ] Deployment completed
- [ ] Copied backend URL: `https://rag-backend.onrender.com`
- [ ] Tested health endpoint: `curl https://your-backend-url/health`

**Status**: _______________

#### ✅ Path C: Self-Hosted VPS
- [ ] VPS provisioned (AWS/DigitalOcean/Linode)
- [ ] SSH access configured  
- [ ] Docker & Docker Compose installed
- [ ] Repository cloned to VPS
- [ ] `.env` file created with production values
- [ ] `docker-compose up -d` executed in `infra/` directory
- [ ] Containers running: `docker ps`
- [ ] Backend responding: `curl http://localhost:8000/health`
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Domain pointing to VPS IP
- [ ] Tested via domain: `curl https://your-backend-domain.com/health`

**Status**: _______________

---

## 📱 Frontend Deployment to Cloudflare Pages

### Configuration in Cloudflare
- [ ] Logged into Cloudflare Dashboard
- [ ] Navigated to Pages section
- [ ] Created new project: "Connect to Git"
- [ ] Selected GitHub repository
- [ ] Configured build settings:
  - [ ] Framework preset: `Next.js`
  - [ ] Build command: `npm run build`
  - [ ] Build output directory: `out`
  - [ ] Root directory: `frontend`
- [ ] Added environment variables:
  - [ ] `NEXT_PUBLIC_API_URL=https://your-backend-url.com`
  - [ ] `NODE_ENV=production`
- [ ] Deployment initiated
- [ ] Build completed successfully (check logs)
- [ ] Deployment URL provided: `https://your-project.pages.dev`

### Testing Frontend
- [ ] Accessed Cloudflare Pages URL in browser
- [ ] Page loaded without errors
- [ ] Console shows no critical errors (F12)
- [ ] Network tab shows API calls going to backend URL

---

## 🔐 CORS & Security Configuration

### Backend CORS Setup
- [ ] `ALLOWED_ORIGINS` environment variable set to:
  ```
  https://your-project.pages.dev,https://yourdomain.com
  ```
- [ ] Backend restarted (Railway/Render auto-restart on env change)
- [ ] Tested CORS with curl:
  ```bash
  curl -H "Origin: https://your-project.pages.dev" \
       https://your-backend-url/health -v
  ```

### Additional Security Headers (Optional)
- [ ] HTTPS enforced on both frontend and backend
- [ ] X-Frame-Options header set
- [ ] X-Content-Type-Options header set
- [ ] Content-Security-Policy configured

---

## 🔗 Domain Configuration (Optional)

### Connect Custom Domain
- [ ] Domain registered (GoDaddy/Namecheap/etc.)
- [ ] Cloudflare nameservers added to domain registrar
- [ ] Domain verified in Cloudflare dashboard
- [ ] Pages custom domain configured: `Pages → Settings → Custom domains`
  - [ ] Added `chatbot.yourdomain.com` (or similar)
- [ ] Cloudflare DNS records verified
- [ ] Custom domain accessible in browser
- [ ] SSL certificate automatically issued by Cloudflare

### Backend Domain (Optional)
- [ ] If not using Railway/Render URL, add custom domain to backend
- [ ] Update `NEXT_PUBLIC_API_URL` to use custom backend domain
- [ ] Redeploy frontend to apply changes

---

## 🧪 Testing & Validation

### Health Checks
- [ ] Backend health endpoint: `curl https://your-backend-url/health`
  - Expected: `{"status":"ok","version":"0.1.0"}`
- [ ] Frontend loads: `https://your-project.pages.dev`
- [ ] No console errors in browser DevTools

### API Integration Testing
- [ ] Chat endpoint test:
  ```bash
  curl -X POST https://your-backend-url/api/chat \
       -H "Content-Type: application/json" \
       -d '{"query":"test question"}'
  ```
- [ ] Search endpoint test:
  ```bash
  curl -X POST https://your-backend-url/api/search \
       -H "Content-Type: application/json" \
       -d '{"query":"test"}'
  ```

### User Flow Testing
- [ ] Visited frontend URL
- [ ] Entered a question in chat interface
- [ ] Received response with citations
- [ ] Citations link to correct documents
- [ ] Performance acceptable (< 3 seconds response time)

### Cross-Browser Testing (Optional)
- [ ] Chrome/Chromium: ✅
- [ ] Firefox: ✅
- [ ] Safari: ✅
- [ ] Mobile browser: ✅

---

## 📊 Monitoring & Logging

### Set Up Monitoring
- [ ] Cloudflare Pages analytics viewed
- [ ] Backend logs accessible:
  - [ ] Railway: Dashboard → Logs
  - [ ] Render: Services → Logs
  - [ ] Self-hosted: `docker-compose logs -f backend`
- [ ] Error notifications configured (optional):
  - [ ] Email alerts enabled
  - [ ] Sentry/Datadog integrated (optional)
- [ ] Performance metrics baseline established

### Backup & Recovery
- [ ] Database backup strategy defined
- [ ] Vector database (Chroma) backup plan:
  - [ ] Automated backups configured (if available)
  - [ ] Manual backup procedure documented
- [ ] Deployment rollback process tested

---

## 🔧 CI/CD Pipeline (Optional)

### GitHub Actions Setup
- [ ] `.github/workflows/deploy.yml` created
- [ ] Secrets configured in GitHub:
  - [ ] `CLOUDFLARE_API_TOKEN`
  - [ ] `CLOUDFLARE_ACCOUNT_ID`
  - [ ] Railway/Render deploy tokens (if applicable)
- [ ] Workflow tested on a test push
- [ ] Build notifications configured (email/Slack)

### Automatic Deployments
- [ ] Verified auto-deploy on `main` push
- [ ] Verified staging builds on feature branches (optional)
- [ ] Rollback procedure documented

---

## 📋 Final Verification Checklist

### Functionality
- [ ] Chat interface works end-to-end
- [ ] Search returns results
- [ ] Citations display correctly
- [ ] Error messages are user-friendly
- [ ] File uploads work (if applicable)

### Performance
- [ ] Frontend load time < 3 seconds
- [ ] API response time < 2 seconds
- [ ] No memory leaks detected
- [ ] Supports expected concurrent users

### Security
- [ ] HTTPS/TLS enabled
- [ ] CORS properly configured
- [ ] API keys/secrets not exposed
- [ ] Input validation working
- [ ] Rate limiting configured (optional)

### Infrastructure
- [ ] All environment variables set correctly
- [ ] Database connectivity verified
- [ ] Vector database (Chroma) working
- [ ] Logging enabled and accessible
- [ ] Backups configured

---

## 🎉 Deployment Complete!

You've successfully deployed your RAG chatbot! Here's what you now have:

```
YOUR RAG CHATBOT
├── Frontend: https://your-project.pages.dev
├── Backend: https://your-backend-url.com  
├── Database: Vector DB (Chroma) running
└── Monitoring: Logs accessible via dashboards
```

### 📚 Useful URLs to Bookmark
- Cloudflare Pages Dashboard: https://dash.cloudflare.com/pages
- Railway Dashboard: https://railway.app/dashboard (if using Railway)
- Render Dashboard: https://dashboard.render.com (if using Render)
- Your deployed app: https://your-project.pages.dev

### 🚀 Next Steps
1. Share the app with users
2. Monitor logs for errors
3. Set up error tracking (Sentry, etc.)
4. Plan feature updates
5. Schedule regular backups
6. Monitor performance metrics

### 📞 Support Resources
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://docs.render.com/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)

---

**Questions?** Check the [CLOUDFLARE_DEPLOYMENT_GUIDE.md](CLOUDFLARE_DEPLOYMENT_GUIDE.md) for detailed troubleshooting.
