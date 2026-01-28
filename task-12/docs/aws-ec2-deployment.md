# AWS EC2 Deployment Guide - Complete Step-by-Step

Complete guide for deploying your n8n automation on AWS EC2 with SSL certificate.

---

## 📋 Prerequisites

- AWS Account ([aws.amazon.com](https://aws.amazon.com))
- Credit card (for account verification)
- Domain name (for SSL certificate)
- Basic knowledge of SSH and Linux commands

---

## 🚀 Step 1: Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Complete registration:
   - Email address
   - Password
   - Account name
   - Credit card (required, but Free Tier available)
   - Phone verification
4. Wait for account activation (usually instant)

---

## 🖥️ Step 2: Launch EC2 Instance

### 2.1 Navigate to EC2

1. Sign in to [AWS Console](https://console.aws.amazon.com)
2. In the search bar at top, type: `EC2`
3. Click on "EC2" service

### 2.2 Launch Instance

1. Click orange "Launch Instance" button (top right)

### 2.3 Configure Instance

**Name and tags**:
- Name: `n8n-automation` (or your preferred name)

**Application and OS Images (Amazon Machine Image - AMI)**:
- Click "Browse more AMIs"
- Search for: `Ubuntu`
- Select: **"Ubuntu Server 22.04 LTS (HVM), SSD Volume Type"**
- Architecture: **64-bit (x86)**

**Instance type**:
- For testing: `t2.micro` (Free Tier eligible, but may be too small)
- **Recommended**: `t3.small` (2 vCPU, 2 GB RAM) - ~$15/month
- **Better**: `t3.medium` (2 vCPU, 4 GB RAM) - ~$30/month
- Click "Next: Configure Instance Details"

**Configure Instance Details**:
- Number of instances: `1`
- Network: Select default VPC (or create new if needed)
- Subnet: Choose any availability zone
- Auto-assign Public IP: **Enable**
- Click "Next: Add Storage"

**Add Storage**:
- Size (GiB): `20` (minimum, 30 GB recommended)
- Volume Type: `gp3` (General Purpose SSD)
- Click "Next: Add Tags"

**Add Tags** (Optional):
- Click "Add tag"
- Key: `Name`
- Value: `n8n-automation`
- Click "Next: Configure Security Group"

**Configure Security Group**:
- Security group name: `n8n-automation-sg`
- Description: `Security group for n8n automation`

**Add Rules**:
1. **SSH**:
   - Type: `SSH`
   - Protocol: `TCP`
   - Port: `22`
   - Source: Click dropdown → Select "My IP" (or `0.0.0.0/0` for any IP - less secure)

2. **HTTP**:
   - Click "Add rule"
   - Type: `HTTP`
   - Protocol: `TCP`
   - Port: `80`
   - Source: `0.0.0.0/0`

3. **HTTPS**:
   - Click "Add rule"
   - Type: `HTTPS`
   - Protocol: `TCP`
   - Port: `443`
   - Source: `0.0.0.0/0`

4. **Custom TCP (n8n)**:
   - Click "Add rule"
   - Type: `Custom TCP`
   - Port: `5678`
   - Source: `0.0.0.0/0` (or restrict to your IP)

- Click "Review and Launch"

**Review Instance Launch**:
- Review all settings
- Click "Launch"

### 2.4 Create Key Pair

1. **Create a new key pair**:
   - Select "Create a new key pair"
   - Key pair name: `n8n-automation-key`
   - Key pair type: `RSA`
   - Private key file format: `.pem`
   - Click "Download Key Pair"
   - **CRITICAL**: Save the `.pem` file securely (you can't download it again)

2. **Or use existing key pair**:
   - Select your existing key pair from dropdown

3. Click "Launch Instances"

### 2.5 Wait for Instance

1. Click "View Instances" button
2. Wait for "Instance State" to show "Running" (green checkmark)
3. Note the **Public IPv4 address** (e.g., `54.123.45.67`)
4. Note the **Public IPv4 DNS** (e.g., `ec2-54-123-45-67.compute-1.amazonaws.com`)

---

## 🔐 Step 3: Connect to EC2 Instance

### 3.1 Set Key Permissions (Mac/Linux)

```bash
chmod 400 ~/Downloads/n8n-automation-key.pem
```

**Windows**: No need to change permissions, but ensure key is in secure location.

### 3.2 Connect via SSH

**Mac/Linux**:
```bash
ssh -i ~/Downloads/n8n-automation-key.pem ubuntu@YOUR_PUBLIC_IP
```

**Windows (Git Bash/WSL)**:
```bash
ssh -i /path/to/n8n-automation-key.pem ubuntu@YOUR_PUBLIC_IP
```

**Windows (PowerShell with OpenSSH)**:
```powershell
ssh -i C:\path\to\n8n-automation-key.pem ubuntu@YOUR_PUBLIC_IP
```

Replace `YOUR_PUBLIC_IP` with your instance's public IP address.

### 3.3 First Connection

- Type `yes` when prompted: "Are you sure you want to continue connecting (yes/no/[fingerprint])?"
- You should see: `Welcome to Ubuntu...`

---

## 🛠️ Step 4: Initial Server Setup

Run these commands on your EC2 instance:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl wget nano ufw htop

# Set timezone (optional)
sudo timedatectl set-timezone UTC
```

---

## 🐳 Step 5: Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version

# Log out and log back in for group changes to take effect
exit
```

**Reconnect via SSH**:
```bash
ssh -i ~/path/to/key.pem ubuntu@YOUR_PUBLIC_IP
```

**Verify Docker works without sudo**:
```bash
docker ps
```

---

## 📦 Step 6: Clone Your Repository

```bash
# Create project directory
mkdir -p ~/projects
cd ~/projects

# Clone your repository (replace with your actual repo URL)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME/task-12

# Or if different structure:
# git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git task-12
# cd task-12
```

**If repository is private**, you'll need to set up SSH keys or use HTTPS with credentials.

---

## ⚙️ Step 7: Configure Application

```bash
# Navigate to project directory
cd ~/projects/task-12

# Create data directory
mkdir -p data

# Create config.json from example
cp data/config.json.example data/config.json

# Edit config.json with your API keys
nano data/config.json
```

Add your configuration:
```json
{
  "GROQ_API_KEY": "gsk_your_actual_groq_api_key_here"
}
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

```bash
# Initialize reply counter
echo '{"count": 0, "target": 50}' > data/replyCount.json

# Initialize replied IDs tracker
echo '[]' > data/repliedIds.json
```

---

## 🍪 Step 8: Upload Cookie Files

From your **local machine**, upload cookies:

```bash
# Upload cookies.json
scp -i ~/path/to/n8n-automation-key.pem data/cookies.json ubuntu@YOUR_PUBLIC_IP:~/projects/task-12/data/

# Verify upload
ssh -i ~/path/to/key.pem ubuntu@YOUR_PUBLIC_IP "ls -la ~/projects/task-12/data/"
```

**Or create manually on server**:
```bash
# On server
nano data/cookies.json
# Paste your cookies JSON array
# Save: Ctrl+X, Y, Enter
```

---

## 🔥 Step 9: Configure Firewall (UFW)

```bash
# Allow SSH (important - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow n8n port (optional - if not using reverse proxy)
sudo ufw allow 5678/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 🚀 Step 10: Build and Start Application

```bash
# Navigate to project directory
cd ~/projects/task-12

# Build Docker image
docker compose build

# Start services in background
docker compose up -d

# View logs
docker compose logs -f
```

Press `Ctrl+C` to exit logs view.

---

## ✅ Step 11: Verify Deployment

1. **Check if container is running**:
   ```bash
   docker ps
   ```
   You should see `n8n-puppeteer` container running.

2. **Check logs**:
   ```bash
   docker compose logs n8n
   ```

3. **Access n8n**:
   - Open browser: `http://YOUR_PUBLIC_IP:5678`
   - You should see n8n setup page

4. **Complete n8n setup**:
   - Create admin account
   - Set password
   - Complete initial setup

---

## 🌐 Step 12: Set Up Domain and DNS

### 12.1 Get Your Domain

If you don't have a domain:
- Purchase from: Namecheap, GoDaddy, Google Domains, etc.
- Or use a subdomain from a free service (not recommended for production)

### 12.2 Configure DNS

1. **Get your EC2 instance's Public IP**:
   - From EC2 Console → Instances → Your instance
   - Copy the "Public IPv4 address"

2. **Add A Record in your domain's DNS**:
   - Log in to your domain registrar's DNS management
   - Add new record:
     - **Type**: `A`
     - **Name**: `@` (for root domain) or `n8n` (for subdomain like `n8n.yourdomain.com`)
     - **Value**: Your EC2 Public IP (e.g., `54.123.45.67`)
     - **TTL**: `3600` (or default)

3. **Wait for DNS propagation**:
   - Usually takes 5-30 minutes
   - Check with: `nslookup yourdomain.com` or `dig yourdomain.com`

---

## 🔒 Step 13: Install Nginx and Certbot

```bash
# Install Nginx
sudo apt install nginx -y

# Install Certbot for Let's Encrypt SSL
sudo apt install certbot python3-certbot-nginx -y

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check Nginx status
sudo systemctl status nginx
```

---

## 🔐 Step 14: Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/n8n
```

Add this configuration (replace `yourdomain.com` with your actual domain):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long-running requests
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}
```

Save and exit: `Ctrl+X`, `Y`, `Enter`

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

---

## 🔒 Step 15: Get SSL Certificate with Let's Encrypt

```bash
# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# 1. Enter email address (for renewal notifications)
# 2. Agree to terms (type 'A' and press Enter)
# 3. Share email with EFF? (optional, type 'Y' or 'N')
# 4. Redirect HTTP to HTTPS? (recommended: type '2' and press Enter)
```

Certbot will:
- Obtain SSL certificate
- Configure Nginx for HTTPS
- Set up auto-renewal

### 15.1 Verify SSL Certificate

1. Visit: `https://yourdomain.com`
2. You should see n8n with a valid SSL certificate (lock icon in browser)
3. Check certificate: Click lock icon → Certificate → Valid

### 15.2 Test Auto-Renewal

```bash
# Test certificate renewal (dry run)
sudo certbot renew --dry-run
```

If successful, auto-renewal is working.

---

## 📥 Step 16: Import Workflow in n8n

1. **Access n8n**:
   - Via domain: `https://yourdomain.com`
   - Or via IP: `http://YOUR_PUBLIC_IP:5678`

2. **Import workflow**:
   - Go to **Workflows** → **Import from File**
   - Upload `workflows/twitter-ai-reply-automation.json`
   - Workflow will be imported

3. **Configure workflow**:
   - Review all nodes
   - Adjust **Limit** node if needed
   - Configure **Schedule Trigger** if needed

4. **Test workflow**:
   - Click **Execute Workflow** to test
   - Check logs: `docker compose logs -f n8n`

---

## 🔄 Step 17: Set Up Auto-Start (Optional)

Create a systemd service to auto-start on reboot:

```bash
# Create service file
sudo nano /etc/systemd/system/n8n-automation.service
```

Add this content:

```ini
[Unit]
Description=n8n Automation Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/projects/task-12
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
```

Save and exit, then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable n8n-automation.service

# Start service
sudo systemctl start n8n-automation.service

# Check status
sudo systemctl status n8n-automation.service
```

---

## 💾 Step 18: Set Up Backups

Create backup script:

```bash
# Create backup directory
mkdir -p ~/backups

# Create backup script
nano ~/backup-n8n.sh
```

Add this content:

```bash
#!/bin/bash
BACKUP_DIR="$HOME/backups/n8n"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="$HOME/projects/task-12"

mkdir -p $BACKUP_DIR

# Backup data directory
tar -czf $BACKUP_DIR/data_$DATE.tar.gz -C $PROJECT_DIR data/

# Backup n8n_data directory
tar -czf $BACKUP_DIR/n8n_data_$DATE.tar.gz -C $PROJECT_DIR n8n_data/

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable:

```bash
chmod +x ~/backup-n8n.sh
```

Test backup:

```bash
~/backup-n8n.sh
```

Set up cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /home/ubuntu/backup-n8n.sh >> /home/ubuntu/backup.log 2>&1
```

---

## 📊 Step 19: Monitoring and Maintenance

### Check Container Status

```bash
# View running containers
docker ps

# View container stats
docker stats

# View logs
docker compose logs -f n8n
```

### Check System Resources

```bash
# View resource usage
htop

# Check disk usage
df -h

# Check memory
free -h
```

### Update Application

```bash
cd ~/projects/task-12

# Pull latest code (if using Git)
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
```

---

## 🐛 Troubleshooting

### Can't Connect via SSH

1. **Check Security Group**:
   - EC2 Console → Security Groups
   - Ensure port 22 is open to your IP

2. **Check Instance Status**:
   - Ensure instance is "Running"
   - Check "Status Checks" are passing

3. **Verify Key Pair**:
   - Ensure you're using correct `.pem` file
   - Check file permissions: `chmod 400 key.pem`

### Container Won't Start

```bash
# Check logs
docker compose logs n8n

# Check if port is in use
sudo netstat -tulpn | grep 5678

# Rebuild without cache
docker compose build --no-cache
docker compose up -d
```

### Out of Memory

```bash
# Check memory usage
free -h

# If low on memory, upgrade instance:
# EC2 Console → Instance → Actions → Instance Settings → Change Instance Type
# Choose: t3.medium (4 GB RAM) or larger
```

### Can't Access n8n

1. **Check firewall**:
   ```bash
   sudo ufw status
   ```

2. **Check if container is running**:
   ```bash
   docker ps
   ```

3. **Check Nginx**:
   ```bash
   sudo systemctl status nginx
   sudo nginx -t
   ```

4. **Check security group**:
   - Ensure ports 80, 443, and/or 5678 are open

### SSL Certificate Issues

```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Manually renew
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

### DNS Not Resolving

```bash
# Check DNS propagation
nslookup yourdomain.com
dig yourdomain.com

# Verify A record points to correct IP
# Wait 30 minutes for propagation
```

---

## 💰 Cost Optimization

### AWS Free Tier

- **EC2**: 750 hours/month of t2.micro (may be too small)
- **EBS Storage**: 30 GB free
- **Data Transfer**: 15 GB out free

### Cost Estimates (After Free Tier)

| Instance Type | RAM | vCPU | Monthly Cost (approx) |
|--------------|-----|------|----------------------|
| t3.micro      | 1 GB | 2    | ~$7.50/month         |
| t3.small      | 2 GB | 2    | ~$15/month           |
| t3.medium     | 4 GB | 2    | ~$30/month           |

**Recommendation**: Start with `t3.small` (2 GB RAM) for ~$15/month.

### Reduce Costs

1. **Stop instance when not in use** (for testing):
   - EC2 Console → Instance → Instance State → Stop
   - You'll only pay for storage (~$2/month for 20 GB)

2. **Use Reserved Instances** (for long-term):
   - Save up to 72% compared to On-Demand

3. **Monitor usage**:
   - AWS Cost Explorer
   - Set up billing alerts

---

## 🔐 Security Best Practices

1. **Restrict SSH Access**:
   - In Security Group, only allow your IP for port 22
   - Use SSH keys, not passwords

2. **Keep System Updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Use Strong Passwords**:
   - For n8n admin account
   - For AWS account

4. **Enable AWS CloudWatch**:
   - Monitor instance metrics
   - Set up alarms

5. **Regular Backups**:
   - Automated daily backups (already set up)
   - Test restore process

6. **Limit Security Group Rules**:
   - Only open necessary ports
   - Restrict source IPs when possible

---

## 📝 Quick Reference Commands

```bash
# Start services
cd ~/projects/task-12 && docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f n8n

# Restart services
docker compose restart

# Rebuild and restart
docker compose up -d --build

# Check status
docker ps

# Backup
~/backup-n8n.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Check Nginx
sudo systemctl status nginx
sudo nginx -t
sudo systemctl reload nginx

# Check SSL certificate
sudo certbot certificates
sudo certbot renew --dry-run
```

---

## ✅ Deployment Checklist

- [ ] AWS account created
- [ ] EC2 instance launched (t3.small or larger)
- [ ] Security group configured (SSH, HTTP, HTTPS, 5678)
- [ ] Connected via SSH
- [ ] Docker and Docker Compose installed
- [ ] Repository cloned/uploaded
- [ ] `data/config.json` configured with API keys
- [ ] Cookie files uploaded
- [ ] Firewall (UFW) configured
- [ ] Application built and started
- [ ] n8n accessible via IP
- [ ] Domain DNS configured (A record)
- [ ] Nginx installed and configured
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] HTTPS working (https://yourdomain.com)
- [ ] Workflow imported
- [ ] Auto-start service configured (optional)
- [ ] Backups configured
- [ ] Monitoring set up

---

## 🎉 You're Done!

Your n8n automation is now:
- ✅ Running on AWS EC2
- ✅ Accessible via HTTPS with SSL certificate
- ✅ Fully automated
- ✅ Backed up daily

**Next Steps**:
1. Test workflow execution
2. Monitor resource usage
3. Set up CloudWatch alarms (optional)
4. Configure email notifications (optional)

---

## 📚 Additional Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [n8n Documentation](https://docs.n8n.io/)

---

**Need Help?** Check the main [README.md](../README.md) or [setup.md](setup.md) for workflow-specific setup.
