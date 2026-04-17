# 🔧 Cloudflare Pages Build Failure - Troubleshooting

Your deployment to Cloudflare Pages is failing during the build. Here's how to fix it:

---

## ⚠️ Common Issues & Solutions

### Issue 1: Wrong Build Settings in Cloudflare Pages

**This is the most common issue.** You need to configure the build settings correctly.

#### ✅ Correct Cloudflare Pages Build Configuration

1. Go to **Cloudflare Dashboard** → **Pages**
2. Select your **rag-chatbot-frontend** project
3. Go to **Settings** → **Builds & Deployments** → **Build Settings**

**Set these values EXACTLY:**

| Setting | Value |
|---------|-------|
| **Framework preset** | `Next.js` |
| **Build command** | `npm run build` |
| **Build output directory** | `.next` |
| **Root directory** | `frontend` |
| **Node.js version** | `20.11.1` or higher |

4. In **Environment Variables**, add:
   ```
   NEXT_PUBLIC_API_URL = https://your-backend-url.com
   NODE_ENV = production
   ```

5. **Save & Redeploy**

---

### Issue 2: Check Cloudflare Pages Logs

1. Go to **Pages Project** → **Deployments**
2. Click the **failed deployment**
3. Click **View build log**
4. Look for error messages

#### Common Build Log Errors:

**Error: `Cannot find module 'next'`**
→ Dependencies not installing. Check Node.js version is 18+

**Error: `TypeScript compilation failed`**
→ Type errors in code. Install dependencies locally and run `npm run build`

**Error: `NEXT_PUBLIC_API_URL is undefined`**
→ Environment variable not set. Add it in Cloudflare Pages settings

**Error: `build command failed`**
→ Run `npm run build` locally to see the actual error

---

## 🔍 Troubleshooting Steps

### Step 1: Test Build Locally

First, ensure it builds on your machine:

```bash
cd frontend
npm install
npm run build
```

If this fails locally, fix the error before deploying to Cloudflare.

### Step 2: Check for Linting Errors

```bash
npm run lint
```

There might be ESLint errors preventing the build.

### Step 3: Verify Dependencies

```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Step 4: Check Environment Variables

Your app needs `NEXT_PUBLIC_API_URL` to work:

```bash
# Test locally
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
```

### Step 5: Review TypeScript

```bash
# Check for TypeScript errors
npx tsc --noEmit
```

---

## ✅ Step-by-Step Fix

### 1. Fix Build Settings in Cloudflare Pages

Go to your Pages project settings and update:

```
Root directory: frontend
Framework preset: Next.js
Build command: npm run build
Build output directory: .next
Node.js version: 20.11.1
```

### 2. Add Environment Variables in Cloudflare Pages

In **Settings** → **Environment variables**, add:

**Production:**
```
NEXT_PUBLIC_API_URL = https://your-backend-domain.com
NODE_ENV = production
```

**Preview (optional):**
```
NEXT_PUBLIC_API_URL = http://localhost:8000
NODE_ENV = development
```

### 3. Clear Cache & Redeploy

1. Go to **Deployments** tab
2. Click the three dots on latest failed deployment
3. Select **Redeploy** or **Clear cache and redeploy**

### 4. Monitor the Build

Watch the build log in real-time:
1. Go to **Deployments**
2. Click the new deployment
3. Watch the build log

---

## 📋 Cloudflare Pages Settings Checklist

Use this while configuring your Pages project:

### Build & Deployments
- [ ] Framework preset: `Next.js`
- [ ] Build command: `npm run build`
- [ ] Build output directory: `.next`
- [ ] Root directory: `frontend`
- [ ] Node.js version: `20` or higher

### Environment Variables (Production)
- [ ] `NEXT_PUBLIC_API_URL` = `https://your-backend-url`
- [ ] `NODE_ENV` = `production`

### Git Configuration
- [ ] Builds on: `Push to production`
- [ ] Production branch: `main`
- [ ] Auto-deploy enabled: `Yes`

### Custom Domain (Optional)
- [ ] Domain configured
- [ ] SSL certificate active
- [ ] DNS CNAME verified

---

## 🚨 If Build Still Fails

### Check the Build Log Error Message

The build log will tell you exactly what's wrong. Common issues:

1. **TypeScript errors** → Run `npx tsc --noEmit` locally to fix
2. **ESLint errors** → Run `npm run lint` locally to fix  
3. **Missing dependencies** → Run `npm install` locally
4. **Wrong Node version** → Update to Node 20 in settings
5. **Environment variable missing** → Add to Cloudflare Pages

### Ask Yourself:

- [ ] Does it build locally with `npm run build`?
- [ ] Are all environment variables set in Cloudflare?
- [ ] Is the root directory set to `frontend`?
- [ ] Is Node.js version 18+ in Cloudflare settings?
- [ ] Did you click "Save" after changing settings?

---

## 🔗 Useful Links

- **Cloudflare Pages Build Settings**: https://dash.cloudflare.com/
  - Pages → Your Project → Settings → Builds & Deployments
  
- **Next.js Build Troubleshooting**: https://nextjs.org/docs/deployment/static-exports

- **Cloudflare Pages Docs**: https://developers.cloudflare.com/pages/framework-guides/deploy-a-nextjs-site/

---

## 💡 Quick Checklist

Before redeploying, ensure:

- ✅ You can run `npm run build` locally without errors
- ✅ Root directory is `frontend` (not `/` or blank)
- ✅ Build output is `.next` (not `out` or `build`)
- ✅ Environment variables are set in Cloudflare
- ✅ Node.js version is indicated as `Node 20` or later
- ✅ Build command is exactly `npm run build`
- ✅ You clicked "Save" after making changes

---

## After Fix: Test Your Deployment

Once the build succeeds:

1. **Visit your Cloudflare Pages URL**: `https://your-project.pages.dev`
2. **Check browser console** (F12): Any errors?
3. **Check Network tab** (F12): API calls going to correct backend?
4. **Try the chat**: Ask a question to test the backend connection

---

**Still stuck?** Check the actual error message in Cloudflare's build log - that's your best clue!
