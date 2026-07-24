# Deployment Guide — Turnkey Statistical Analysis Pipeline

## Table of Contents
1. [Local Deployment](#local-deployment)
2. [Streamlit Cloud](#streamlit-cloud)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Platforms](#cloud-platforms)
5. [Production Checklist](#production-checklist)

---

## Local Deployment

### Development Mode
```bash
# Basic run
streamlit run app.py

# With custom port
streamlit run app.py --server.port 8080

# With headless mode (no browser auto-open)
streamlit run app.py --server.headless true
```

### Production Mode
```bash
# Enable CORS and disable CORS protection
streamlit run app.py   --server.port 8501   --server.address 0.0.0.0   --server.enableCORS false   --server.enableXsrfProtection false   --browser.gatherUsageStats false
```

---

## Streamlit Cloud

Streamlit Cloud is the fastest way to deploy this application.

### Steps
1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/turnkey-analysis.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Configure Secrets (if needed)**
   - Go to App Settings → Secrets
   - Add any API keys or configuration

---

## Docker Deployment

### Dockerfile
```dockerfile
# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     build-essential     && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the application
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build & Run
```bash
# Build image
docker build -t turnkey-analysis .

# Run container
docker run -p 8501:8501 turnkey-analysis

# Run with volume mount for data
docker run -p 8501:8501 -v $(pwd)/data:/app/data turnkey-analysis
```

### Docker Compose
```yaml
version: '3.8'

services:
  turnkey-analysis:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## Cloud Platforms

### AWS Deployment

#### Option 1: AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 turnkey-analysis

# Create environment
eb create turnkey-analysis-env

# Deploy
eb deploy
```

#### Option 2: AWS ECS (Fargate)
1. Push Docker image to ECR
2. Create ECS cluster
3. Define task with container port 8501
4. Create service with Application Load Balancer

#### Option 3: AWS EC2
```bash
# Launch EC2 instance (t3.medium recommended)
# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start

# Run container
sudo docker run -d -p 80:8501 --name turnkey-analysis turnkey-analysis
```

### Azure Deployment

#### Azure Container Instances
```bash
# Login
az login

# Create resource group
az group create --name turnkey-rg --location eastus

# Create container
az container create   --resource-group turnkey-rg   --name turnkey-analysis   --image turnkey-analysis:latest   --ports 8501   --ip-address Public
```

#### Azure App Service
```bash
# Create App Service
az webapp create   --resource-group turnkey-rg   --plan turnkey-plan   --name turnkey-analysis-app   --deployment-container-image-name turnkey-analysis:latest
```

### Google Cloud Platform

#### Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/turnkey-analysis

# Deploy to Cloud Run
gcloud run deploy turnkey-analysis   --image gcr.io/PROJECT_ID/turnkey-analysis   --platform managed   --region us-central1   --allow-unauthenticated   --port 8501
```

---

## Production Checklist

### Security
- [ ] Disable CORS in production if behind reverse proxy
- [ ] Enable XSRF protection
- [ ] Use HTTPS (SSL/TLS)
- [ ] Set up authentication if data is sensitive
- [ ] Review file upload size limits

### Performance
- [ ] Set `browser.gatherUsageStats` to false
- [ ] Configure appropriate server resources
- [ ] Enable caching for static assets
- [ ] Monitor memory usage with large datasets

### Reliability
- [ ] Set up health checks
- [ ] Configure auto-restart policies
- [ ] Set up logging and monitoring
- [ ] Create backup strategy for uploaded data

### Scaling
- [ ] Use load balancer for multiple instances
- [ ] Consider horizontal scaling for high traffic
- [ ] Set resource limits in container orchestration

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | 8501 | Server port |
| `STREAMLIT_SERVER_ADDRESS` | 0.0.0.0 | Bind address |
| `STREAMLIT_SERVER_HEADLESS` | false | Disable browser auto-open |
| `STREAMLIT_BROWSER_GATHERUSAGESTATS` | true | Usage analytics |
| `STREAMLIT_SERVER_ENABLECORS` | true | CORS protection |
| `STREAMLIT_SERVER_ENABLEXSRFPROTECTION` | true | XSRF protection |

---

## Reverse Proxy Configuration

### Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Apache
```apache
<VirtualHost *:80>
    ServerName your-domain.com

    ProxyPreserveHost On
    ProxyPass / http://localhost:8501/
    ProxyPassReverse / http://localhost:8501/

    <Proxy *>
        Order deny,allow
        Allow from all
    </Proxy>
</VirtualHost>
```
