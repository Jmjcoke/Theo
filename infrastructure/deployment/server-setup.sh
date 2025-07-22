#!/bin/bash
# DigitalOcean Server Setup Script for Theo
# This script sets up the initial server environment

set -e

echo "🚀 Starting Theo server setup..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Install Nginx for reverse proxy
echo "🌐 Installing Nginx..."
apt-get install -y nginx

# Install Certbot for SSL
echo "🔒 Installing Certbot for SSL..."
apt-get install -y certbot python3-certbot-nginx

# Install additional utilities
echo "🛠️ Installing utilities..."
apt-get install -y curl wget git jq htop

# Create theo user for deployments
echo "👤 Creating theo user..."
useradd -m -s /bin/bash theo
usermod -aG docker theo

# Create application directories
echo "📁 Creating application directories..."
mkdir -p /opt/theo
chown theo:theo /opt/theo
mkdir -p /opt/theo/data
chown theo:theo /opt/theo/data

# Configure firewall
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443

# Create nginx configuration for reverse proxy
echo "⚙️ Configuring Nginx reverse proxy..."
cat > /etc/nginx/sites-available/theo << 'EOF'
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Frontend proxy
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Direct backend health check
    location /health {
        proxy_pass http://localhost:8001/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/theo /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

# Set up log rotation
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/theo << 'EOF'
/opt/theo/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 theo theo
    postrotate
        docker-compose -f /opt/theo/docker-compose.yml restart
    endscript
}
EOF

# Create systemd service for auto-restart
echo "⚡ Creating systemd service..."
cat > /etc/systemd/system/theo.service << 'EOF'
[Unit]
Description=Theo Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/theo
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=theo
Group=theo

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable theo.service

echo "✅ Server setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure your domain name to point to this server"
echo "2. Run: certbot --nginx -d yourdomain.com"
echo "3. Deploy your application using the CI/CD pipeline"
echo ""
echo "Server is ready for deployment! 🎉"