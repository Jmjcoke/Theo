# Theo Deployment Infrastructure

This directory contains all the necessary files and scripts for deploying Theo to DigitalOcean.

## Prerequisites

Before setting up the CI/CD pipeline, you need:

1. **DigitalOcean Droplet** - Ubuntu 20.04 LTS or newer
2. **Docker Hub Account** - For storing Docker images
3. **Domain Name** - Pointed to your server's IP address
4. **GitHub Repository Secrets** - Configure the required secrets

## Required GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
DOCKER_USERNAME          # Your Docker Hub username
DOCKER_PASSWORD          # Your Docker Hub password/access token
SSH_PRIVATE_KEY          # SSH private key for server access
SSH_USER                 # SSH username (usually 'root' or 'theo')
SERVER_HOST              # Your server's domain name or IP address
```

## Server Setup

### 1. Initial Server Configuration

Run the server setup script on your DigitalOcean droplet:

```bash
# On your server (as root)
curl -fsSL https://raw.githubusercontent.com/yourusername/theo/main/infrastructure/deployment/server-setup.sh | bash
```

Or manually:

```bash
# Copy and run the script
scp infrastructure/deployment/server-setup.sh root@your-server:/tmp/
ssh root@your-server 'bash /tmp/server-setup.sh'
```

### 2. SSL Certificate Setup

After the server is set up and your domain points to the server:

```bash
# On your server
./ssl-setup.sh yourdomain.com
```

## Deployment Process

The deployment happens automatically when you push to the `main` branch:

1. **Build Stage**: GitHub Actions builds and tests both frontend and backend
2. **Docker Images**: Creates and pushes Docker images to Docker Hub
3. **Deploy Stage**: Deploys containers to your DigitalOcean server
4. **Health Check**: Validates deployment success
5. **Notification**: Reports deployment status

## Manual Deployment

You can also trigger deployments manually:

1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "Deploy to DigitalOcean" workflow
4. Click "Run workflow"

## Architecture

```
Internet → Nginx (SSL Termination) → Docker Containers
                                   ├── Frontend (Port 3000)
                                   └── Backend (Port 8001)
```

### Services

- **Frontend**: React app served by Nginx
- **Backend**: FastAPI application with Uvicorn
- **Reverse Proxy**: Nginx handles SSL and routing
- **Database**: SQLite (file-based, in Docker volume)

### Ports

- **80/443**: Nginx reverse proxy (public)
- **3000**: Frontend container (internal)
- **8001**: Backend container (internal)

## Health Checks

The deployment includes comprehensive health checks:

- **Backend**: `GET /health` returns `{"status": "ok"}`
- **Frontend**: Homepage displays "Welcome to Theo."
- **SSL**: HTTPS redirection and security headers
- **Docker**: Container health checks with automatic restart

## Monitoring

### Application Logs

```bash
# View application logs
docker-compose -f /opt/theo/docker-compose.yml logs -f

# View specific service logs
docker logs theo-backend
docker logs theo-frontend
```

### Nginx Logs

```bash
# Access logs
tail -f /var/log/nginx/access.log

# Error logs
tail -f /var/log/nginx/error.log
```

### System Status

```bash
# Check service status
systemctl status theo
systemctl status nginx
systemctl status docker

# Check container status
docker ps
docker stats
```

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs for build errors
2. Verify all required secrets are configured
3. Ensure server is accessible via SSH
4. Check server disk space and resources

### Health Checks Fail

1. Check container logs: `docker logs theo-backend`
2. Verify containers are running: `docker ps`
3. Test health endpoints manually:
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:3000/
   ```

### SSL Issues

1. Verify domain points to server IP
2. Check firewall allows ports 80 and 443
3. Regenerate certificate:
   ```bash
   certbot delete --cert-name yourdomain.com
   ./ssl-setup.sh yourdomain.com
   ```

### Database Issues

1. Check SQLite database permissions:
   ```bash
   ls -la /opt/theo/data/
   ```
2. Verify volume mount in docker-compose.yml

## Rollback

If a deployment fails, you can rollback manually:

```bash
# On your server
cd /opt/theo
docker-compose down
docker pull yourdockerhub/theo-backend:previous-tag
docker pull yourdockerhub/theo-frontend:previous-tag
# Update docker-compose.yml with previous tags
docker-compose up -d
```

## Scaling

For production scaling considerations:

1. **Database**: Migrate from SQLite to PostgreSQL/Supabase
2. **Load Balancing**: Add multiple app instances behind load balancer
3. **CDN**: Use CDN for static assets
4. **Monitoring**: Implement proper monitoring and alerting
5. **Backups**: Automated database backups

## Security

The deployment includes security best practices:

- ✅ Non-root containers
- ✅ SSL/TLS encryption
- ✅ Security headers
- ✅ Firewall configuration
- ✅ Automatic security updates
- ✅ Container health checks

## Support

For issues with this deployment setup:

1. Check the GitHub Actions logs
2. Review server logs
3. Verify all prerequisites are met
4. Check the troubleshooting section above