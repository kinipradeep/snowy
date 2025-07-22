# Deployment Guide - Contact Manager

This guide covers deploying the Contact Manager application to various production environments.

## 🚀 Quick Start (Replit Deployment)

The easiest way to deploy is using Replit's built-in deployment:

1. **Configure Environment Variables**
   ```bash
   # In Replit Secrets tab
   DATABASE_URL=postgresql://user:password@host:port/database
   SESSION_SECRET=your-secure-random-key-min-32-chars
   ```

2. **Deploy Application**
   - Click the "Deploy" button in Replit
   - Application will be available at your-repl.replit.app

## 🐳 Docker Deployment

### Dockerfile
Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

### Docker Compose
Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://contact_user:contact_pass@db:5432/contact_manager
      - SESSION_SECRET=${SESSION_SECRET}
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=contact_user
      - POSTGRES_PASSWORD=contact_pass
      - POSTGRES_DB=contact_manager
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Deploy with Docker
```bash
# Build and start services
docker-compose up -d

# Initialize database
docker-compose exec web python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## ☁️ Cloud Deployments

### AWS (Elastic Beanstalk)

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB Application**
   ```bash
   eb init contact-manager --region us-east-1
   ```

3. **Create Environment**
   ```bash
   eb create production
   ```

4. **Configure Environment Variables**
   ```bash
   eb setenv DATABASE_URL=postgresql://... SESSION_SECRET=...
   ```

5. **Deploy**
   ```bash
   eb deploy
   ```

### Google Cloud Platform (Cloud Run)

1. **Build Container**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/contact-manager
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy contact-manager \
     --image gcr.io/PROJECT-ID/contact-manager \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DATABASE_URL=postgresql://...,SESSION_SECRET=...
   ```

### Heroku

1. **Create Application**
   ```bash
   heroku create your-contact-manager
   ```

2. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:standard-0
   ```

3. **Configure Environment**
   ```bash
   heroku config:set SESSION_SECRET=your-secure-key
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Initialize Database**
   ```bash
   heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

## 🔧 Production Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
SESSION_SECRET=secure-random-key-minimum-32-characters

# Optional Messaging Providers
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone

# AWS SES (if using)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=False
```

### Database Setup

#### PostgreSQL Production Setup
```sql
-- Create database and user
CREATE DATABASE contact_manager;
CREATE USER contact_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE contact_manager TO contact_user;

-- Connect to the database
\c contact_manager;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO contact_user;
```

#### Database Migrations
```bash
# Create all tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# For future migrations, consider using Flask-Migrate
pip install Flask-Migrate
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Web Server Configuration

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/contact-manager/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Systemd Service
Create `/etc/systemd/system/contact-manager.service`:

```ini
[Unit]
Description=Contact Manager Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/contact-manager
Environment="DATABASE_URL=postgresql://..."
Environment="SESSION_SECRET=your-secret"
ExecStart=/path/to/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable contact-manager
sudo systemctl start contact-manager
```

## 📊 Monitoring & Logging

### Application Logging
```python
# Configure in production
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/contact-manager.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Database Monitoring
```bash
# PostgreSQL monitoring queries
SELECT * FROM pg_stat_activity WHERE state = 'active';
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables;
```

### Health Check Endpoint
Add to your Flask app:
```python
@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
```

## 🔐 Security Checklist

### SSL/TLS
- [ ] Use HTTPS in production
- [ ] Configure proper SSL certificates
- [ ] Set secure headers (HSTS, CSP, etc.)

### Database Security
- [ ] Use strong database passwords
- [ ] Restrict database access by IP
- [ ] Enable database SSL connections
- [ ] Regular security updates

### Application Security
- [ ] Use secure session secrets (32+ characters)
- [ ] Enable CSRF protection
- [ ] Validate all user inputs
- [ ] Use parameterized database queries
- [ ] Regular dependency updates

### Messaging Security
- [ ] Secure API keys in environment variables
- [ ] Use HTTPS for all API calls
- [ ] Validate phone numbers and emails
- [ ] Rate limit messaging endpoints

## 🚨 Backup Strategy

### Database Backups
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > /backups/contact_manager_$DATE.sql
find /backups -name "contact_manager_*.sql" -mtime +7 -delete
```

### File Backups
```bash
# Backup application files
tar -czf contact_manager_files_$DATE.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  /path/to/contact-manager
```

## 📈 Performance Optimization

### Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_contacts_organization_id ON contacts(organization_id);
CREATE INDEX idx_contacts_phone ON contacts(phone);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_templates_organization_id ON templates(organization_id);
```

### Caching
Consider implementing Redis for:
- Session storage
- Frequently accessed data
- Rate limiting counters

### Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
```

## 🔄 CI/CD Pipeline

The project includes GitHub Actions for:
- Automated testing
- Security scanning
- Code quality checks
- Deployment automation

See `.github/workflows/ci.yml` for configuration.

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database connectivity
4. Validate messaging provider configurations
5. Check security group/firewall settings

---

**Ready for Production** ✅
Your Contact Manager deployment is enterprise-ready with multi-tenant architecture, comprehensive messaging, and robust security features.