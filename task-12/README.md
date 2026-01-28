# X.com AI/ML Reply Automation with n8n

An automated workflow that scrapes your X.com (Twitter) home feed, identifies AI/ML-related tweets using Groq AI, generates intelligent replies, and posts them automatically. Built with n8n, Puppeteer, and Docker.

## 🚀 Features

- **Automated Feed Scraping**: Scrapes your X.com home feed using Puppeteer
- **AI-Powered Classification**: Uses Groq's Llama model to identify AI/ML-related tweets
- **Smart Reply Generation**: Generates contextual, natural replies using AI
- **Duplicate Prevention**: Tracks replied tweets to avoid duplicates
- **Rate Limiting**: Built-in delays and batch limits to respect X.com's rate limits
- **Cookie-Based Auth**: Secure authentication using exported browser cookies
- **Scheduled Execution**: Runs automatically every 4 hours (configurable)

## 📋 Prerequisites

- **Docker** and **Docker Compose** installed
- **Groq API Key** from [console.groq.com](https://console.groq.com)
- **X.com Account** (logged in session for cookie export)

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd task-12
```

### 2. Set Up Configuration Files

Create `data/config.json` from the example:

```bash
cp data/config.json.example data/config.json
```

Edit `data/config.json` and add your Groq API key:

```json
{
  "GROQ_API_KEY": "gsk_your_actual_api_key_here"
}
```

### 3. Export X.com Cookies

You need to export your X.com session cookies for authentication:

**Option A: Using Browser DevTools**
1. Log in to X.com in your browser
2. Open DevTools (F12) → Application tab → Cookies → `https://x.com`
3. Copy all cookies (especially `auth_token`, `ct0`, `twid`)
4. Save as `data/cookies.json` in the format:
   ```json
   [
     {
       "name": "auth_token",
       "value": "your_auth_token_value",
       "domain": ".x.com",
       "path": "/",
       "secure": true,
       "httpOnly": true,
       "sameSite": "None"
     },
     ...
   ]
   ```

**Option B: Using Browser Extension**
- Use extensions like "Cookie-Editor" or "EditThisCookie"
- Export cookies while logged in to X.com
- Save as `data/cookies.json` in JSON array format

### 4. Initialize Data Files

Create the required data files:

```bash
# Create data directory if it doesn't exist
mkdir -p data

# Initialize reply counter
echo '{"count": 0, "target": 50}' > data/replyCount.json

# Initialize replied IDs tracker
echo '[]' > data/repliedIds.json
```

### 5. Build and Start

```bash
# Build the Docker image
docker compose build

# Start the services
docker compose up -d

# View logs
docker compose logs -f
```

### 6. Access n8n

Open your browser and navigate to:
```
http://localhost:5678
```

### 7. Import Workflow

1. In n8n, go to **Workflows** → **Import from File**
2. Select `workflows/twitter-ai-reply-automation.json`
3. The workflow will be imported with all nodes configured

### 8. Configure Workflow

- **Limit Node**: Set "Max items" to control how many replies per run (default: 5)
- **Schedule Trigger**: Runs every 4 hours by default (adjustable in the node)

### 9. Activate and Test

1. Click **Active** toggle to enable the workflow
2. Or click **Execute Workflow** to run it manually for testing

## ☁️ Cloud Deployment

### Deploy to Render + Vercel (Free Tier)

Deploy your automation to the cloud for free using Render (hosting) + Vercel (keep-alive service).

**Benefits**:
- ✅ Free hosting on Render
- ✅ Free keep-alive service on Vercel
- ✅ No server management
- ✅ Automatic deployments
- ✅ HTTPS included

**See detailed guide**: [docs/render-vercel-deployment.md](docs/render-vercel-deployment.md)

The guide includes:
- Step-by-step Render deployment
- Vercel keep-alive service setup
- Configuration and troubleshooting
- Complete setup checklist

## 📁 Project Structure

```
.
├── Dockerfile                 # Docker image with n8n + Puppeteer + Chromium
├── docker-compose.yml         # Docker Compose configuration
├── .gitignore                 # Git ignore rules (excludes sensitive files)
├── README.md                  # This file
├── data/                      # Data directory (mounted as /data in container)
│   ├── config.json.example    # Example config file (safe to commit)
│   ├── config.json            # Your actual config (NOT committed)
│   ├── cookies.json           # X.com cookies (NOT committed)
│   ├── replyCount.json        # Reply counter
│   └── repliedIds.json        # Tracked replied tweet IDs
├── docs/
│   ├── setup.md                      # Detailed setup documentation
│   └── render-vercel-deployment.md    # Cloud deployment guide
├── vercel-keepalive/                 # Vercel keep-alive service
│   ├── api/ping.js                   # Ping endpoint
│   ├── vercel.json                   # Cron job configuration
│   └── package.json
├── render.yaml                       # Render deployment configuration
└── workflows/
    └── twitter-ai-reply-automation.json  # n8n workflow definition
```

## 🔒 Security Notes

**Important**: The following files contain sensitive information and are excluded from Git:
- `data/config.json` - Contains your Groq API key
- `data/cookies.json` - Contains your X.com session cookies
- `cookies.json` - Any root-level cookie files

These files are listed in `.gitignore` and will **never** be committed to version control.

## ⚙️ Configuration

### Reply Target

Edit `data/replyCount.json` to set a target:

```json
{
  "count": 0,
  "target": 50
}
```

The workflow stops when `count` reaches `target` (default: 50).

### Batch Size

Adjust the **Limit** node in the workflow to control replies per run (recommended: 5-10).

### Schedule

Modify the **Schedule Trigger** node to change execution frequency (default: every 4 hours).

## 🔄 Workflow Overview

1. **Check counter** - Verifies if target reply count is reached
2. **Load cookies** - Loads X.com authentication cookies
3. **Scrape feed** - Scrapes home feed and extracts tweets
4. **Filter replied** - Removes already-replied tweets
5. **Classify with Groq** - Identifies AI/ML-related tweets
6. **Limit** - Limits to batch size (e.g., 5 tweets)
7. **Generate reply** - Generates AI replies for each tweet
8. **Post replies** - Posts replies to X.com
9. **Persist** - Updates counters and replied IDs

## 🐛 Troubleshooting

### Cookies Not Working

- Ensure cookies are exported while **logged in** to X.com
- Verify `auth_token` cookie is included (required for authentication)
- Check cookie format matches the expected JSON array structure

### Reply Button Not Found

- X.com frequently changes their UI. Update selectors in the "Post replies" node
- Try alternative selectors: `button[data-testid="reply"]`, `[aria-label*="Reply"]`

### Rate Limiting

- Reduce batch size in the **Limit** node
- Increase delays between posts (currently 10-30 seconds)
- Run the schedule less frequently

### Chromium/Browser Issues

- Ensure Docker has proper permissions: `security_opt: seccomp=unconfined` and `cap_add: SYS_ADMIN`
- Check Docker logs: `docker compose logs n8n`

### API Errors

- Verify Groq API key is correct in `data/config.json`
- Check API quota/limits at [console.groq.com](https://console.groq.com)

For more detailed troubleshooting, see [docs/setup.md](docs/setup.md).

## 📊 Monitoring

### Check Reply Count

```bash
cat data/replyCount.json
```

### View Replied IDs

```bash
cat data/repliedIds.json
```

### View n8n Logs

```bash
docker compose logs -f n8n
```

## 🔧 Advanced Configuration

### Custom AI Model

Edit the **Classify with Groq** and **Generate reply** nodes to use different models:
- `llama-3.1-8b-instant` (default, fast)
- `llama-3.1-70b-versatile` (slower, more capable)
- `mixtral-8x7b-32768` (balanced)

### Custom Reply Style

Modify the system prompt in the **Generate reply** node to change reply tone/style.

### Proxy Support

Add proxy configuration to Puppeteer nodes if needed for rate limit avoidance.

## 📝 License

This project is for educational purposes. Use responsibly and in accordance with X.com's Terms of Service.

## ⚠️ Disclaimer

- This tool automates interactions with X.com. Use at your own risk.
- Respect X.com's rate limits and Terms of Service.
- Excessive automation may result in account suspension.
- The authors are not responsible for any consequences of using this tool.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Sensitive files (`config.json`, `cookies.json`) are never committed
- Code follows existing patterns
- Documentation is updated

## 📚 Resources

- [n8n Documentation](https://docs.n8n.io/)
- [Puppeteer Documentation](https://pptr.dev/)
- [Groq API Documentation](https://console.groq.com/docs)
- [n8n-nodes-puppeteer](https://github.com/n8n-io/n8n-nodes-puppeteer)

---

**Made with ❤️ for AI/ML enthusiasts**
