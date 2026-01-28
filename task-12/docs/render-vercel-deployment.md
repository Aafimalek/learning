# Render + Vercel Deployment Guide

Complete guide for deploying your n8n automation on Render (free tier) with a Vercel keep-alive service to prevent sleep.

---

## 🎯 Overview

**Strategy**:
- **Render**: Hosts the n8n workflow automation (free tier, but sleeps after 15 min inactivity)
- **Vercel**: Hosts a dummy app with cron job that pings Render every 2 hours to keep it awake

**Benefits**:
- ✅ Free hosting on Render
- ✅ Free keep-alive service on Vercel
- ✅ No server management
- ✅ Automatic deployments
- ✅ HTTPS included

---

## 📋 Prerequisites

- GitHub account (for repository)
- Render account (sign up at [render.com](https://render.com))
- Vercel account (sign up at [vercel.com](https://vercel.com))
- Groq API key
- X.com cookies exported

---

## 🚀 Part 1: Deploy to Render

### Step 1: Prepare Your Repository

1. **Push your code to GitHub**:
   ```bash
   # If not already a git repo
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Create `render.yaml`** in your project root:
   ```bash
   nano render.yaml
   ```

   Add this content:
   ```yaml
   services:
     - type: web
       name: n8n-automation
       env: docker
       plan: free
       dockerfilePath: ./Dockerfile
       dockerContext: .
       envVars:
         - key: N8N_HOST
           value: 0.0.0.0
         - key: N8N_PORT
           value: 5678
         - key: NODE_FUNCTION_ALLOW_BUILTIN
           value: fs,https
         - key: NODE_FUNCTION_ALLOW_EXTERNAL
           value: puppeteer
         - key: N8N_CUSTOM_EXTENSIONS
           value: /opt/n8n-custom-nodes/node_modules/n8n-nodes-puppeteer
         - key: PUPPETEER_SKIP_CHROMIUM_DOWNLOAD
           value: true
         - key: PUPPETEER_EXECUTABLE_PATH
           value: /usr/bin/chromium-browser
         - key: GROQ_API_KEY
           sync: false  # Will set in dashboard
       disk:
         name: n8n-data
         mountPath: /home/node/.n8n
         sizeGB: 1
       disk:
         name: app-data
         mountPath: /data
         sizeGB: 1
   ```

   Save and commit:
   ```bash
   git add render.yaml
   git commit -m "Add Render configuration"
   git push
   ```

### Step 2: Create Render Account and Service

1. **Sign up for Render**:
   - Go to [render.com](https://render.com)
   - Click "Get Started for Free"
   - Sign up with GitHub (recommended)

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository
   - Render will auto-detect `render.yaml`

3. **Configure Service**:
   - **Name**: `n8n-automation` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty (or `./` if needed)
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`

4. **Add Environment Variables**:
   Click "Advanced" → "Add Environment Variable":
   - `GROQ_API_KEY`: Your Groq API key (mark as "Secret")
   - `N8N_HOST`: `0.0.0.0`
   - `N8N_PORT`: `5678`
   - `NODE_FUNCTION_ALLOW_BUILTIN`: `fs,https`
   - `NODE_FUNCTION_ALLOW_EXTERNAL`: `puppeteer`
   - `N8N_CUSTOM_EXTENSIONS`: `/opt/n8n-custom-nodes/node_modules/n8n-nodes-puppeteer`
   - `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD`: `true`
   - `PUPPETEER_EXECUTABLE_PATH`: `/usr/bin/chromium-browser`

5. **Create Persistent Disks**:
   - Go to "Disks" tab
   - Click "Create Disk"
   - **Name**: `n8n-data`
   - **Mount Path**: `/home/node/.n8n`
   - **Size**: 1 GB
   - Click "Create Disk"
   
   - Create second disk:
   - **Name**: `app-data`
   - **Mount Path**: `/data`
   - **Size**: 1 GB
   - Click "Create Disk"

6. **Deploy**:
   - Click "Create Web Service"
   - Render will start building your Docker image
   - Wait for deployment to complete (5-10 minutes)

### Step 3: Access and Configure n8n

1. **Get Your Render URL**:
   - After deployment, you'll see: `https://n8n-automation.onrender.com`
   - Copy this URL (you'll need it for Vercel)

2. **Access n8n**:
   - Open the URL in browser
   - Complete n8n setup:
     - Create admin account
     - Set password
     - Complete initial setup

3. **Upload Configuration Files**:
   
   **Option A: Via Render Shell** (Recommended):
   - Go to Render Dashboard → Your Service → "Shell"
   - Run:
     ```bash
     # Create data directory structure
     mkdir -p /data
     
     # Create config.json
     cat > /data/config.json << 'EOF'
     {
       "GROQ_API_KEY": "your-groq-api-key-here"
     }
     EOF
     
     # Create replyCount.json
     echo '{"count": 0, "target": 50}' > /data/replyCount.json
     
     # Create repliedIds.json
     echo '[]' > /data/repliedIds.json
     ```

   **Option B: Via n8n UI** (After setup):
   - Use n8n's file operations to create files
   - Or use a Code node to write files

4. **Upload Cookies**:
   - In Render Shell:
     ```bash
     # Create cookies.json
     nano /data/cookies.json
     # Paste your cookies JSON array
     # Save: Ctrl+X, Y, Enter
     ```
   
   **Or via SCP** (if Render supports it):
   ```bash
   # Not typically available on Render free tier
   ```

5. **Import Workflow**:
   - In n8n UI: Workflows → Import from File
   - Upload `workflows/twitter-ai-reply-automation.json`
   - Configure and activate

### Step 4: Test Render Deployment

1. **Check if service is running**:
   - Render Dashboard → Your Service → "Logs"
   - Should see n8n startup messages

2. **Test n8n access**:
   - Visit your Render URL
   - Should see n8n interface

3. **Note**: Service will sleep after 15 minutes of inactivity (we'll fix this with Vercel)

---

## ⚡ Part 2: Create Vercel Keep-Alive Service

### Step 1: Create Vercel Project

1. **Create new directory for Vercel app**:
   ```bash
   mkdir vercel-keepalive
   cd vercel-keepalive
   ```

2. **Create `package.json`**:
   ```bash
   npm init -y
   ```

   Edit `package.json`:
   ```json
   {
     "name": "render-keepalive",
     "version": "1.0.0",
     "description": "Keep-alive service for Render n8n app",
     "main": "api/ping.js",
     "scripts": {
       "dev": "vercel dev"
     },
     "dependencies": {}
   }
   ```

3. **Create API route**:
   ```bash
   mkdir -p api
   ```

   Create `api/ping.js`:
   ```javascript
   export default async function handler(req, res) {
     const RENDER_URL = process.env.RENDER_URL || 'https://n8n-automation.onrender.com';
     
     try {
       // Ping the Render service
       const response = await fetch(RENDER_URL, {
         method: 'GET',
         headers: {
           'User-Agent': 'Vercel-KeepAlive/1.0'
         }
       });
       
       const status = response.status;
       const statusText = response.statusText;
       
       return res.status(200).json({
         success: true,
         message: 'Ping successful',
         renderUrl: RENDER_URL,
         status: status,
         statusText: statusText,
         timestamp: new Date().toISOString()
       });
     } catch (error) {
       return res.status(500).json({
         success: false,
         message: 'Ping failed',
         error: error.message,
         renderUrl: RENDER_URL,
         timestamp: new Date().toISOString()
       });
     }
   }
   ```

4. **Create `vercel.json`** for cron job:
   ```json
   {
     "crons": [
       {
         "path": "/api/ping",
         "schedule": "0 */2 * * *"
       }
     ]
   }
   ```

   This runs every 2 hours.

5. **Create `.env.example`**:
   ```
   RENDER_URL=https://n8n-automation.onrender.com
   ```

6. **Create `.gitignore`**:
   ```
   .env
   .vercel
   node_modules
   ```

7. **Initialize Git and push**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Vercel keep-alive service"
   git remote add origin https://github.com/YOUR_USERNAME/vercel-keepalive.git
   git push -u origin main
   ```

### Step 2: Deploy to Vercel

1. **Sign up for Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub (recommended)

2. **Import Project**:
   - Click "Add New..." → "Project"
   - Import your `vercel-keepalive` repository
   - Framework Preset: "Other"
   - Root Directory: `./`

3. **Configure Environment Variables**:
   - Go to "Settings" → "Environment Variables"
   - Add:
     - `RENDER_URL`: `https://n8n-automation.onrender.com` (your Render URL)
   - Save

4. **Deploy**:
   - Click "Deploy"
   - Wait for deployment (1-2 minutes)

5. **Set Up Cron Job**:
   - Go to "Settings" → "Cron Jobs"
   - Vercel should auto-detect cron from `vercel.json`
   - Verify: Path `/api/ping`, Schedule `0 */2 * * *` (every 2 hours)
   - Enable cron job

### Step 3: Test Keep-Alive Service

1. **Manual Test**:
   - Visit: `https://your-vercel-app.vercel.app/api/ping`
   - Should see JSON response with ping status

2. **Check Cron Job**:
   - Vercel Dashboard → "Cron Jobs"
   - Should see execution history
   - Wait 2 hours or trigger manually to test

3. **Verify Render Stays Awake**:
   - After cron job runs, check Render service
   - It should stay awake (no sleep)

---

## 🔧 Part 3: Configuration and Setup

### Configure n8n on Render

1. **Access n8n**:
   - Go to your Render URL
   - Log in with admin credentials

2. **Import Workflow**:
   - Workflows → Import from File
   - Upload `workflows/twitter-ai-reply-automation.json`

3. **Configure Workflow**:
   - Update all nodes as needed
   - Set up schedule trigger
   - Configure API keys (already in environment)

4. **Upload Data Files**:
   - Use Render Shell to create/upload:
     - `/data/config.json` (with GROQ_API_KEY)
     - `/data/cookies.json` (X.com cookies)
     - `/data/replyCount.json`
     - `/data/repliedIds.json`

### Monitor and Maintain

1. **Check Render Logs**:
   - Render Dashboard → Service → "Logs"
   - Monitor for errors

2. **Check Vercel Logs**:
   - Vercel Dashboard → Project → "Functions" → `/api/ping`
   - View execution logs

3. **Verify Cron Job**:
   - Vercel Dashboard → "Cron Jobs"
   - Check execution history
   - Ensure it runs every 2 hours

---

## 🐛 Troubleshooting

### Render Service Issues

**Service won't start**:
- Check Dockerfile is correct
- Check environment variables
- Review Render logs

**Service sleeps despite keep-alive**:
- Verify Vercel cron job is running
- Check cron job schedule (should be every 2 hours)
- Manually test ping endpoint

**Can't access n8n**:
- Check Render service is running
- Verify URL is correct
- Check firewall/security settings

**Data files missing**:
- Use Render Shell to create files
- Verify disk mounts are correct
- Check file paths in workflow

### Vercel Keep-Alive Issues

**Cron job not running**:
- Verify `vercel.json` has correct cron configuration
- Check Vercel Cron Jobs settings
- Ensure project is on Vercel Pro (free tier has limited cron)

**Ping fails**:
- Verify `RENDER_URL` environment variable
- Check Render service is accessible
- Review Vercel function logs

**Cron schedule not working**:
- Verify cron syntax: `0 */2 * * *` (every 2 hours)
- Test with shorter schedule first: `*/5 * * * *` (every 5 minutes) for testing

---

## 💡 Optimization Tips

### Reduce Render Sleep Time

1. **Increase ping frequency** (if needed):
   - Change cron to `0 * * * *` (every hour)
   - Or `*/30 * * * *` (every 30 minutes)

2. **Add health check endpoint**:
   - Create simple endpoint in n8n
   - Ping that instead of main page

### Cost Optimization

- **Render Free Tier**: 
  - 750 hours/month
  - Services sleep after 15 min inactivity
  - 1 GB disk per service

- **Vercel Free Tier**:
  - Unlimited requests
  - Cron jobs available (may need Pro for frequent cron)
  - 100 GB bandwidth

### Alternative: Render Paid Plan

If you need guaranteed uptime:
- **Starter Plan**: $7/month
- No sleep
- Better performance
- More resources

---

## 📊 Monitoring

### Set Up Alerts

1. **Render**:
   - Dashboard → Service → "Alerts"
   - Set up email notifications

2. **Vercel**:
   - Dashboard → Project → "Settings" → "Notifications"
   - Enable deployment notifications

### Check Service Health

```bash
# Test Render service
curl https://n8n-automation.onrender.com

# Test Vercel ping
curl https://your-vercel-app.vercel.app/api/ping
```

---

## 🔄 Updates and Maintenance

### Update n8n Workflow

1. **Edit workflow in n8n UI**
2. **Or update JSON file**:
   - Edit `workflows/twitter-ai-reply-automation.json`
   - Push to GitHub
   - Render will auto-deploy

### Update Configuration

1. **Environment Variables**:
   - Render Dashboard → Service → "Environment"
   - Update variables
   - Redeploy

2. **Data Files**:
   - Use Render Shell to edit files
   - Or use n8n file operations

### Backup Strategy

1. **Export n8n workflows**:
   - n8n UI → Workflows → Export

2. **Backup data files**:
   - Use Render Shell to download files
   - Or set up automated backup script

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `render.yaml` created and committed
- [ ] Render account created
- [ ] Web service deployed on Render
- [ ] Environment variables configured
- [ ] Persistent disks created
- [ ] n8n accessed and configured
- [ ] Data files uploaded (config.json, cookies.json)
- [ ] Workflow imported
- [ ] Vercel keep-alive app created
- [ ] Vercel project deployed
- [ ] Environment variable set (RENDER_URL)
- [ ] Cron job configured and enabled
- [ ] Keep-alive tested and working
- [ ] Workflow tested and running

---

## 🎉 You're Done!

Your n8n automation is now:
- ✅ Running on Render (free tier)
- ✅ Kept awake by Vercel cron job
- ✅ Fully automated
- ✅ Cost: $0/month (free tier)

**Next Steps**:
1. Monitor Render logs
2. Verify cron job runs every 2 hours
3. Test workflow execution
4. Set up alerts/notifications

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Cron Jobs](https://vercel.com/docs/cron-jobs)
- [n8n Documentation](https://docs.n8n.io/)

---

**Need Help?** Check the main [README.md](../README.md) or [setup.md](setup.md) for workflow-specific setup.
