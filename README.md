# Enterprise IPO Reminder System (GitHub-Only)

**Cloud-native IPO monitoring and notification system** running entirely on GitHub's infrastructure with official API integrations, database persistence, advanced analytics, and comprehensive compliance features.

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Cloud%20Execution-blue)](https://github.com/features/actions)
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

## 📋 **Prerequisites (GitHub-Only)**

### No Local Requirements
- **Zero local setup** - Everything runs on GitHub's cloud infrastructure
- **GitHub Account** - Required for repository access and Actions execution
- **Email Account** - Gmail recommended for automated notifications

### API Keys (Optional but Recommended)
- **BSE API Key**: For official BSE data (stored as GitHub secret)
- **NSE API Key**: For official NSE data (stored as GitHub secret)

---

## 🚀 **Quick Start (GitHub-Only)**

### Automated GitHub Execution

Your IPO Reminder system runs **entirely on GitHub's cloud infrastructure** with no local setup required:

1. **Configure Secrets**: Set up email and API credentials in GitHub repository secrets
2. **Automatic Execution**: System runs daily at 6:00 AM IST via GitHub Actions
3. **Cloud Database**: PostgreSQL and Redis services provided by GitHub Actions
4. **Remote Monitoring**: View execution logs and status in GitHub Actions tab

### GitHub Secrets Setup

Go to your GitHub repository: https://github.com/dilludinesh/ipo-reminder
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SENDER_EMAIL` | Your Gmail address | `your-email@gmail.com` |
| `SENDER_PASSWORD` | Gmail App Password | `abcd-efgh-ijkl-mnop` |
| `RECIPIENT_EMAIL` | Email to receive reminders | `recipient@email.com` |
| `BSE_API_KEY` | BSE API key (optional) | `your-bse-key` |
| `NSE_API_KEY` | NSE API key (optional) | `your-nse-key` |
| `ENCRYPTION_KEY` | 32-char encryption key | `your-32-char-key` |
| `JWT_SECRET_KEY` | JWT signing key | `your-jwt-secret` |

### Gmail App Password Setup
1. Enable 2-Factor Authentication on Gmail
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password for "IPO Reminder"
4. Use this 16-character password as `SENDER_PASSWORD`

---

## ⚙️ **GitHub Actions Automation (Primary Execution)**

### Workflow Features
- ✅ **Cloud-Only Execution**: Runs entirely on GitHub's infrastructure
- ✅ **Automated Daily Execution**: Runs at 6:00 AM IST every day
- ✅ **On-Demand Execution**: Manual trigger available anytime
- ✅ **PostgreSQL Database**: Cloud database service provided by GitHub
- ✅ **Redis Caching**: High-performance cloud caching
- ✅ **Multi-source Data**: Fetches from Zerodha, Moneycontrol, Chittorgarh
- ✅ **Professional Emails**: HTML templates with IPO analysis
- ✅ **Comprehensive Logging**: All activities logged and stored
- ✅ **Error Handling**: Robust error handling and notifications
- ✅ **Artifact Upload**: Logs saved for 30 days

### Workflow Triggers
```yaml
on:
  schedule:
    - cron: '30 0 * * *'  # 6:00 AM IST daily
  workflow_dispatch:       # Manual trigger anytime
  push:
    branches: [ main ]     # Test on code changes
```

### Manual Execution
To run the IPO reminder system manually:
1. Go to **Actions** tab in your GitHub repository
2. Click **Enterprise IPO Reminder** workflow
3. Click **Run workflow** button
4. The system will execute immediately on GitHub's cloud

### Monitoring Your Automation
1. Go to **Actions** tab in your GitHub repository
2. Click **Enterprise IPO Reminder** workflow
3. View run history and detailed logs
4. Download log artifacts if needed
5. Check email delivery status

### Troubleshooting Automation
- **Check Secrets**: Ensure all required secrets are set in repository settings
- **Verify App Password**: Gmail App Password must be valid and current
- **Review Logs**: Detailed error logs in workflow runs
- **Test Manually**: Use workflow dispatch to test immediately
- **Check Permissions**: Repository must allow GitHub Actions to run

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

## 🔧 **System Management (GitHub-Only)**

### Code Updates
To update the system code:
1. Make changes directly in the GitHub repository
2. Commit and push changes to the `main` branch
3. GitHub Actions will automatically test the changes
4. Monitor the Actions tab for execution results

### Log Access
- **Execution Logs**: Available in GitHub Actions run history
- **Artifact Downloads**: Logs saved for 30 days
- **Real-time Monitoring**: View live execution in Actions tab
- **Error Notifications**: Check email for any system failures

### Configuration Updates
All configuration is managed through GitHub repository secrets:
- Update secrets in repository Settings → Secrets and variables → Actions
- Changes take effect on next workflow execution
- No local configuration files needed

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

## 🚀 **Deployment (GitHub-Only)**

### GitHub Actions Deployment
Your system is **fully deployed and running on GitHub**:

- **Infrastructure**: GitHub provides all necessary compute, database, and caching
- **Scaling**: Automatic scaling based on execution demands
- **Reliability**: 99.9% uptime with GitHub's enterprise-grade infrastructure
- **Security**: All data encrypted and secured by GitHub
- **Cost**: Free tier includes unlimited Actions minutes for public repositories

### Execution Schedule
- **Daily**: Automatic execution at 6:00 AM IST
- **On-Demand**: Manual execution anytime via workflow dispatch
- **On-Changes**: Automatic testing on code pushes to main branch

### Data Persistence
- **Database**: PostgreSQL service provided by GitHub Actions
- **Cache**: Redis service for high-performance caching
- **Logs**: Comprehensive logging with 30-day retention
- **Artifacts**: Execution artifacts stored securely

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
