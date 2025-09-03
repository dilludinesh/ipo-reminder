# GitHub Codespaces Setup for IPO Reminder

This project is configured to run entirely in GitHub Codespaces for a fully remote development experience.

## 🚀 Getting Started

1. **Open in Codespaces**: Click the "Code" button on GitHub and select "Open with Codespaces"
2. **Wait for setup**: The container will automatically install dependencies and set up the database
3. **Start developing**: All tools and services are pre-configured

## 🛠️ What's Included

### Development Environment
- **Python 3.11** with all required packages
- **PostgreSQL** database service
- **Redis** caching service
- **VS Code extensions** for Python development
- **GitHub CLI** for repository management
- **Docker** for containerized testing

### Pre-installed Extensions
- Python (with IntelliSense)
- Black Formatter
- isort
- Flake8
- MyPy
- GitHub Actions
- GitHub Copilot

### Services
- **PostgreSQL**: Available at `localhost:5432`
- **Redis**: Available at `localhost:6379`
- **API Server**: Runs on port 8000 (auto-forwarded)

## 🔧 Configuration

The environment is automatically configured with:
- Python virtual environment
- Database setup
- All dependencies installed
- Code formatting and linting enabled

## 🚀 Running the Application

```bash
# Run the IPO reminder system
python -m ipo_reminder

# Run tests
pytest

# Run with coverage
pytest --cov=ipo_reminder --cov-report=html
```

## 📊 Monitoring

- **Logs**: Available in the `logs/` directory
- **Database**: Access via `psql` or database tools
- **Redis**: Monitor via `redis-cli`

## 🔒 Secrets Management

For production deployment, configure GitHub repository secrets:
- `SENDER_EMAIL`
- `SENDER_PASSWORD`
- `RECIPIENT_EMAIL`
- `BSE_API_KEY` (optional)
- `NSE_API_KEY` (optional)

## 📝 Development Workflow

1. **Code in Codespaces**: All development happens in the cloud
2. **Commit and push**: Changes are automatically synced to GitHub
3. **GitHub Actions**: Automated testing and deployment on push
4. **Remote execution**: The IPO reminder runs daily via GitHub Actions

This setup ensures everything runs remotely on GitHub infrastructure, from development to production execution.
