# Enterprise IPO Reminder System

**Enterprise-grade IPO monitoring and notification system** with official API integrations, database persistence, advanced analytics, and comprehensive compliance features.

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-blue)](https://github.com/features/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-red)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🚀 **Enterprise Features (v3.0)**

### 🏢 **Enterprise Architecture**
- ✅ **Official API Integration**: BSE and NSE official APIs with circuit breaker pattern
- ✅ **Database Persistence**: PostgreSQL with SQLAlchemy ORM and connection pooling
- ✅ **Redis Caching**: High-performance caching with memory fallback
- ✅ **Microservices Design**: Modular architecture with async processing
- ✅ **Fault Tolerance**: Circuit breakers, retries, and graceful degradation

### 🔒 **Security & Compliance**
- ✅ **Audit Logging**: Comprehensive audit trails with tamper-proof checksums
- ✅ **Data Encryption**: Encrypted sensitive data storage
- ✅ **Input Validation**: Robust input sanitization and validation
- ✅ **Compliance Reporting**: Automated compliance reports and monitoring
- ✅ **Access Control**: Role-based access with JWT authentication

### 📊 **Advanced Analytics**
- 🧠 **Deep Learning Analysis**: ML-powered IPO analysis and risk assessment
- � **Real-time Metrics**: Prometheus-style monitoring and alerting
- 🎯 **Investment Recommendations**: AI-driven investment suggestions
- � **Performance Analytics**: Comprehensive system performance tracking
- 🔍 **Predictive Insights**: Trend analysis and market predictions

### 🔔 **Professional Notifications**
- 📧 **Rich HTML Templates**: Professional email templates with responsive design
- 📱 **Multi-channel Alerts**: Email, SMS, and webhook notifications
- 🎨 **Custom Branding**: White-label solution with custom themes
- � **Detailed Reports**: Comprehensive IPO analysis reports
- 🔄 **Automated Scheduling**: Flexible scheduling with cron expressions

### 🛠️ **DevOps & Monitoring**
- � **System Monitoring**: Real-time health checks and performance metrics
- � **Intelligent Alerting**: Smart alerting with cooldown and escalation
- 📊 **Dashboard Integration**: Grafana/Prometheus dashboard support
- 🔄 **Auto-scaling**: Horizontal scaling with load balancing
- � **Comprehensive Logging**: Structured logging with ELK stack integration

---

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Scrapers  │    │  Official APIs  │    │  Data Sources   │
│                 │    │                 │    │                 │
│ • Zerodha       │◄──►│ • BSE API       │◄──►│ • BSE           │
│ • Moneycontrol  │    │ • NSE API       │    │ • NSE           │
│ • Chittorgarh   │    │ • Circuit       │    │ • SEBI          │
│ • Fallback      │    │   Breaker       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                     │
         └────────────────────────┼─────────────────────┘
                                  │
                    ┌─────────────────┐
                    │ Enterprise      │
                    │ Orchestrator    │
                    │                 │
                    │ • Async         │
                    │   Processing    │
                    │ • Load          │
                    │   Balancing     │
                    │ • Fault         │
                    │   Tolerance     │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │ Advanced        │
                    │ Analytics       │
                    │                 │
                    │ • ML Analysis   │
                    │ • Risk Scoring  │
                    │ • Recommendations│
                    └─────────────────┘
                              │
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Professional    │    │ Enterprise      │
                    │ Notifications   │    │ Database        │
                    │                 │    │                 │
                    │ • HTML Emails   │◄──►│ • PostgreSQL     │
                    │ • SMS Alerts    │    │ • Redis Cache    │
                    │ • Webhooks      │    │ • Audit Logs     │
                    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │ Monitoring &    │
                    │ Compliance      │
                    │                 │
                    │ • Prometheus    │
                    │ • Alert Manager │
                    │ • Audit Reports │
                    └─────────────────┘
```

---

## 📋 **Prerequisites**

### System Requirements
- **Python**: 3.11 or higher
- **PostgreSQL**: 15+ with PostGIS extension
- **Redis**: 7.0+ with persistence enabled
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 10GB free space for logs and data

### API Keys (Optional but Recommended)
- **BSE API Key**: For official BSE data
- **NSE API Key**: For official NSE data

---

## 🚀 **Quick Start**

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/dilludinesh/ipo-reminder.git
cd ipo-reminder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. GitHub Automation Setup (Recommended)

For **completely automated IPO reminders**, set up GitHub Actions:

#### Configure GitHub Secrets
1. Go to your GitHub repository: https://github.com/dilludinesh/ipo-reminder
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SENDER_EMAIL` | Your Gmail address | `your-email@gmail.com` |
| `SENDER_PASSWORD` | Gmail App Password | `abcd-efgh-ijkl-mnop` |
| `RECIPIENT_EMAIL` | Email to receive reminders | `recipient@email.com` |
| `BSE_API_KEY` | BSE API key (optional) | `your-bse-key` |
| `NSE_API_KEY` | NSE API key (optional) | `your-nse-key` |

#### Gmail App Password Setup
1. Enable 2-Factor Authentication on Gmail
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password for "IPO Reminder"
4. Use this 16-character password as `SENDER_PASSWORD`

#### Automated Schedule
The system runs automatically:
- **Daily at 9:00 AM IST** (3:30 AM UTC)
- **Manual trigger** available in GitHub Actions
- **On every push** to main branch (for testing)

### 3. Local Testing (Optional)

```bash
# Set up local database
python setup_database.py setup

# Create .env file
cp .env.example .env
# Edit .env with your email credentials

# Run locally
python -m ipo_reminder
```

---

## ⚙️ **GitHub Actions Automation**

### Workflow Features
- ✅ **Automated Daily Execution**: Runs at 9:00 AM IST every day
- ✅ **PostgreSQL Database**: Enterprise-grade database setup
- ✅ **Redis Caching**: High-performance caching layer
- ✅ **Multi-source Data**: Fetches from Zerodha, Moneycontrol, Chittorgarh
- ✅ **Professional Emails**: HTML templates with IPO analysis
- ✅ **Comprehensive Logging**: All activities logged and stored
- ✅ **Error Handling**: Robust error handling and notifications
- ✅ **Artifact Upload**: Logs saved for 30 days

### Workflow Triggers
```yaml
on:
  schedule:
    - cron: '30 3 * * *'  # 9:00 AM IST daily
  workflow_dispatch:       # Manual trigger
  push:
    branches: [ main ]     # Test on push
```

### Monitoring Your Automation
1. Go to **Actions** tab in your GitHub repository
2. Click **Enterprise IPO Reminder** workflow
3. View run history and detailed logs
4. Download log artifacts if needed
5. Check email delivery status

### Troubleshooting Automation
- **Check Secrets**: Ensure all required secrets are set
- **Verify App Password**: Gmail App Password must be valid
- **Review Logs**: Detailed error logs in workflow runs
- **Test Manually**: Use workflow dispatch to test immediately

---

## 📊 **System Architecture**

## ⚙️ **Configuration Options**

### Core Configuration
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SENDER_EMAIL` | Email address for sending notifications | - | Yes |
| `SENDER_PASSWORD` | Email password/app password | - | Yes |
| `RECIPIENT_EMAIL` | Email address to receive notifications | - | Yes |
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 | No |

### Enterprise Configuration
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BSE_API_KEY` | BSE official API key | - | No |
| `NSE_API_KEY` | NSE official API key | - | No |
| `ENCRYPTION_KEY` | 32-char encryption key | - | Yes |
| `JWT_SECRET_KEY` | JWT signing key | - | Yes |
| `ENTERPRISE_MODE` | Enable enterprise features | true | No |

### Monitoring Configuration
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONITORING_ENABLED` | Enable system monitoring | true | No |
| `AUDIT_ENABLED` | Enable audit logging | true | No |
| `METRICS_RETENTION_DAYS` | Metrics retention period | 30 | No |
| `ALERT_COOLDOWN_MINUTES` | Alert cooldown period | 60 | No |

---

## 📊 **API Endpoints**

### System Status
```bash
GET /api/v1/health
GET /api/v1/status
GET /api/v1/metrics
```

### IPO Data
```bash
GET /api/v1/ipos
GET /api/v1/ipos/{id}
POST /api/v1/ipos/analyze
```

### Audit & Compliance
```bash
GET /api/v1/audit/trail
GET /api/v1/compliance/report
POST /api/v1/compliance/export
```

### Monitoring
```bash
GET /api/v1/monitoring/health
GET /api/v1/monitoring/metrics
GET /api/v1/monitoring/alerts
```

---

## 🔧 **Development**

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ipo_reminder --cov-report=html

# Run specific test file
pytest tests/test_enterprise_orchestrator.py
```

### Code Quality
```bash
# Format code
black ipo_reminder/
isort ipo_reminder/

# Lint code
flake8 ipo_reminder/

# Type checking
mypy ipo_reminder/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Run migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

---

## 📈 **Monitoring & Alerting**

### Health Checks
The system provides comprehensive health monitoring:

- **Database Connectivity**: Connection pool status and query performance
- **Cache Performance**: Hit rates, memory usage, and eviction stats
- **API Health**: Circuit breaker status and response times
- **System Resources**: CPU, memory, and disk usage
- **Business Metrics**: IPO processing rates and success rates

### Alert Types
- **System Alerts**: Database issues, cache failures, API outages
- **Performance Alerts**: High latency, low throughput, resource exhaustion
- **Security Alerts**: Failed authentication, suspicious activities
- **Business Alerts**: IPO processing failures, email delivery issues

### Metrics Dashboard
Access metrics at `/api/v1/metrics` or integrate with:
- **Prometheus**: Native Prometheus metrics endpoint
- **Grafana**: Pre-built dashboards available
- **ELK Stack**: Structured logging for Kibana visualization

---

## 🔒 **Security Features**

### Data Protection
- **Encryption at Rest**: All sensitive data encrypted using AES-256
- **Encryption in Transit**: TLS 1.3 for all network communications
- **Key Management**: Secure key rotation and management
- **Data Masking**: PII data masked in logs and reports

### Access Control
- **JWT Authentication**: Token-based authentication with expiration
- **Role-Based Access**: Granular permissions system
- **API Rate Limiting**: Configurable rate limits per endpoint
- **IP Whitelisting**: Restrict access to trusted networks

### Audit & Compliance
- **Complete Audit Trail**: All actions logged with tamper-proof checksums
- **Compliance Reports**: Automated generation of compliance reports
- **Data Retention**: Configurable retention policies
- **GDPR Compliance**: Data portability and right to erasure

---

## 🚀 **Deployment Options**

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python setup_database.py setup

EXPOSE 8000
CMD ["python", "-m", "ipo_reminder.enterprise_orchestrator"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ipo-reminder
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ipo-reminder
  template:
    metadata:
      labels:
        app: ipo-reminder
    spec:
      containers:
      - name: ipo-reminder
        image: your-registry/ipo-reminder:latest
        envFrom:
        - secretRef:
            name: ipo-reminder-secrets
        ports:
        - containerPort: 8000
```

### Cloud Deployment
- **AWS**: ECS, EKS, or Lambda
- **GCP**: Cloud Run, GKE, or Cloud Functions
- **Azure**: Container Instances, AKS, or Functions
- **Heroku**: Standard deployment with add-ons

---

## 📞 **Support & Documentation**

### Documentation
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

### Support
- **Issues**: [GitHub Issues](https://github.com/your-username/ipo-reminder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ipo-reminder/discussions)
- **Email**: support@ipo-reminder.com

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **BSE India** and **NSE India** for providing official APIs
- **Chittorgarh** for IPO data and analysis
- **Zerodha** and **Moneycontrol** for additional data sources
- **Open source community** for amazing libraries and tools

---

*Built with ❤️ for the Indian investment community*
