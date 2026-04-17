# ⚡ Cloudflare Pages Build Failure - QUICK FIX

**The build is failing and your chatbot isn't appearing.** Here's the fastest way to fix it.

---

## 🎯 Most Common Cause

**Wrong build settings in Cloudflare Pages.** The build output directory is probably wrong.

---

## ✅ Quick Fix (5 minutes)

### Step 1: Go to Cloudflare Dashboard

1. Open https://dash.cloudflare.com/
2. Click **Pages**
3. Click your **rag-chatbot-frontend** project
4. Go to **Settings** → **Builds & Deployments**

### Step 2: Check Build Settings

Look at these settings and **make sure they match exactly**:

```
Framework preset:        Next.js
Build command:           npm run build
Build output directory:  .next              (NOT "out" or ".next/static")
Root directory:          frontend           (NOT "/" or blank)
Node.js version:         20.11.1 or higher
```

**If they don't match, change them now and click SAVE.**

### Step 3: Add Environment Variable

1. Go to **Settings** → **Environment variables**
2. Add this variable for **Production**:

```
NEXT_PUBLIC_API_URL = https://your-backend-url.com
```

(Replace `your-backend-url.com` with your actual backend URL)

3. Click **Save**

### Step 4: Redeploy

1. Go to **Deployments** tab
2. Find the latest **failed** deployment
3. Click the **...** (three dots) menu
4. Select **Redeploy**
5. Watch the build log - should show success this time

---

## 🔍 If Build Still Fails

Check the **Build Log**:

1. Go to **Deployments**
2. Click the failed/running deployment
3. Click **View build log**
4. Read the error message carefully

### Most Common Errors:

| Error | Fix |
|-------|-----|
| `Cannot find module` | Run `npm install` locally first |
| `TypeScript error` | Run `npm run build` locally to fix errors |
| `Cannot find NEXT_PUBLIC_API_URL` | Add env var in Cloudflare Pages settings |
| `Build timed out` | Your app is too slow. Optimize it. |
| `out of memory` | Reduce bundle size or increase memory |

---

## 🚀 Test Locally First

Before troubleshooting more, test locally:

```bash
cd frontend
npm install
npm run build
```

**It must build locally first.** If it fails locally, fix those errors first.

---

## ✨ Common Settings Screenshot

Your Cloudflare Pages settings should look like this:

```
┌─ BUILDS & DEPLOYMENTS ──────────────────────────┐
│                                                  │
│ Framework preset:         [Next.js ▼]           │
│ Build command:            npm run build          │
│ Build output directory:   .next                  │
│ Root directory:           frontend               │
│ Node.js version:          20.11.1                │
│                                                  │
│ ✓ Auto-deploy on push                           │
│                                                  │
│                        [SAVE AND DEPLOY] [SAVE] │
└──────────────────────────────────────────────────┘
```

---

## 📞 Debugging Checklist

- [ ] Root directory is `frontend` (not blank, not `/`)
- [ ] Build output is `.next` (not `out`, not `.next/static`)
- [ ] Build command is `npm run build` (exact)
- [ ] Node.js version is 20+ (check what's set)
- [ ] `NEXT_PUBLIC_API_URL` env var is set
- [ ] You clicked SAVE after making changes
- [ ] You're redeploying (not just saving)

---

## 🎯 Expected Result

After the fix, you should see:

1. **Build succeeds** ✅ (green checkmark in deployments)
2. **Site live** ✅ (can visit `https://your-project.pages.dev`)
3. **Chatbot appears** ✅ (see the chat interface)
4. **Can send messages** ✅ (if backend is running)

---

## 🆘 Still Not Working?

### Check Build Log Error
The build log in Cloudflare tells you why it failed:
- Go to **Deployments** → click failed deployment → **View build log**
- Look for red ERROR lines

### Test the Build Locally
```bash
cd frontend
npm install
npm run build
```

If this fails locally, fix it first before trying Cloudflare again.

### Common Local Errors:

**TypeScript error:**
```bash
npm run lint
npx tsc --noEmit
```

**Dependency issue:**
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

**Your next action:** 
→ **Open https://dash.cloudflare.com/ and verify your build settings match exactly**

That fixes 90% of build failures!
