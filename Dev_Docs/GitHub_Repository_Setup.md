# GitHub Repository Setup Guide

## Overview
This guide provides step-by-step instructions for setting up GitHub to manage your EDMS repository with proper organization, collaboration features, and CI/CD integration.

## 1. Repository Creation and Initial Setup

### Create Repository on GitHub

```bash
# Option 1: Create via GitHub CLI (if installed)
gh repo create jinkaiteo/edms --public --description "21 CFR Part 11 Compliant Electronic Document Management System"

# Option 2: Create via GitHub Web Interface
# 1. Go to https://github.com/new
# 2. Repository name: edms-system
# 3. Description: "21 CFR Part 11 Compliant Electronic Document Management System"
# 4. Choose Public or Private based on your needs
# 5. Initialize with README: No (we'll add our own)
# 6. Add .gitignore: Python
# 7. Choose a license: MIT or your preferred license
```

### Initialize Local Repository

```bash
# Initialize git in your project directory
git init

# Add remote origin
git remote add origin https://github.com/jinkaiteo/edms.git

# Create and switch to main branch
git checkout -b main

# Add all development docs
git add .
git commit -m "Initial commit: EDMS development documentation"

# Push to GitHub
git push -u origin main
```

## 2. Repository Structure Setup

### Create Essential Files

```bash
# Create essential repository files
touch README.md
touch CONTRIBUTING.md
touch CHANGELOG.md
touch LICENSE
touch SECURITY.md
touch .gitignore
touch .env.example
```

### README.md Template

```markdown
# Electronic Document Management System (EDMS)

A 21 CFR Part 11 compliant Electronic Document Management System built with Django and React.

## 🚀 Features

- **21 CFR Part 11 Compliance**: Electronic signatures, audit trails, and data integrity
- **Document Lifecycle Management**: Review, approval, and workflow automation
- **Advanced Search**: Elasticsearch-powered document discovery
- **Role-Based Access Control**: Secure user and permission management
- **Multi-Factor Authentication**: Enhanced security with Azure AD integration
- **Encrypted Storage**: Secure file storage with integrity verification

## 🏗️ Architecture

- **Backend**: Django REST Framework with PostgreSQL
- **Frontend**: React with TypeScript and Tailwind CSS
- **Workflow Engine**: Django-River for document workflows
- **Search**: Elasticsearch for document indexing
- **Cache**: Redis for performance optimization
- **Storage**: Encrypted file system with backup

## 📚 Documentation

- [Development Setup](Dev_Docs/6_Environment_Setup_Scripts.md)
- [API Documentation](Dev_Docs/2_EDMS_API_Specifications.md)
- [Database Schema](Dev_Docs/1_EDMS_Database_Schema_Complete.md)
- [Configuration Templates](Dev_Docs/Missing_Configuration_Templates.md)
- [Testing Guide](Dev_Docs/9_Testing_Framework_Setup.md)
- [Deployment Guide](Dev_Docs/Deployment_Configurations.md)

## 🚦 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+
- Redis 7+
- Elasticsearch 8+

### Development Setup

```bash
# Clone the repository
git clone https://github.com/jinkaiteo/edms.git
cd edms

# Run setup script
bash scripts/infrastructure-setup.sh

# Start development environment
bash scripts/start-development.sh --init
```

### Docker Setup

```bash
# Start all services with Docker Compose
podman-compose up -d

# Initialize database
bash scripts/initialize-database.sh

# Create test users
bash scripts/create-test-users.sh
```

## 🏭 Production Deployment

See [Deployment Guide](Dev_Docs/Deployment_Configurations.md) for:
- Kubernetes deployment manifests
- CI/CD pipeline configuration
- Production hardening checklist
- Monitoring and backup setup

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npx playwright test
```

## 📋 Project Status

- ✅ Architecture and design complete
- ✅ Development documentation ready
- 🏗️ Core backend development in progress
- ⏳ Frontend development starting
- ⏳ Testing framework implementation
- ⏳ Deployment pipeline setup

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛡️ Security

For security concerns, please review our [Security Policy](SECURITY.md).

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/jinkaiteo/edms/wiki)
- **Issues**: [GitHub Issues](https://github.com/jinkaiteo/edms/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jinkaiteo/edms/discussions)
```

### CONTRIBUTING.md Template

```markdown
# Contributing to EDMS

Thank you for your interest in contributing to the Electronic Document Management System!

## Development Process

1. **Fork** the repository
2. **Create** a feature branch from `develop`
3. **Make** your changes with proper tests
4. **Submit** a pull request

## Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature development branches
- `hotfix/*` - Critical production fixes
- `release/*` - Release preparation branches

## Code Standards

### Backend (Python/Django)

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Maintain test coverage above 85%
- Document all public APIs

```python
# Example function with proper typing and documentation
def create_document(
    title: str, 
    document_type: DocumentType, 
    author: User
) -> Document:
    """
    Create a new document in the EDMS.
    
    Args:
        title: The document title
        document_type: Type of document being created
        author: User creating the document
        
    Returns:
        Created document instance
        
    Raises:
        ValidationError: If document data is invalid
    """
    pass
```

### Frontend (React/TypeScript)

- Use TypeScript for all components
- Follow React hooks best practices
- Implement proper error boundaries
- Use Tailwind CSS for styling

```tsx
// Example component with proper TypeScript
interface DocumentCardProps {
  document: Document;
  onEdit?: (id: string) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ 
  document, 
  onEdit 
}) => {
  // Component implementation
};
```

## Testing Requirements

### Backend Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
pytest -m "security"
```

### Frontend Testing
```bash
# Run unit tests
npm test

# Run E2E tests
npx playwright test
```

## Commit Message Format

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

Examples:
```
feat(documents): add document versioning functionality

- Implement version creation workflow
- Add version history tracking
- Update API endpoints for version management

Closes #123
```

## Pull Request Process

1. **Update** documentation for any new features
2. **Add** tests for new functionality
3. **Ensure** all tests pass
4. **Update** CHANGELOG.md
5. **Request** review from maintainers

## Security Guidelines

- Never commit secrets or credentials
- Follow OWASP security guidelines
- Report security vulnerabilities privately
- Use proper authentication for all endpoints

## Getting Help

- Join our [Discussions](https://github.com/jinkaiteo/edms/discussions)
- Check existing [Issues](https://github.com/jinkaiteo/edms/issues)
- Review the [Wiki](https://github.com/jinkaiteo/edms/wiki)
```

### .gitignore Template

```gitignore
# EDMS Specific
storage/
certificates/
*.key
*.pem
*.p12

# Environment files
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Virtual environments
venv/
ENV/
env/
.venv

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity

# React build
/frontend/build
/frontend/.env.local
/frontend/.env.development.local
/frontend/.env.test.local
/frontend/.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/
coverage.xml
*.cover
.hypothesis/

# Kubernetes
*.yaml.backup

# Logs
*.log
logs/

# Docker
.docker/

# Backup files
*.bak
*.backup
*.tmp
```

## 3. Branch Strategy and Protection Rules

### Branch Protection Setup

```bash
# Using GitHub CLI to set up branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["continuous-integration"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null
```

### Git Flow Configuration

```bash
# Set up Git Flow
git flow init

# Use these branch names:
# Production branch: main
# Development branch: develop
# Feature prefix: feature/
# Release prefix: release/
# Hotfix prefix: hotfix/
# Support prefix: support/

# Create initial develop branch
git checkout -b develop
git push -u origin develop
```

## 4. GitHub Actions CI/CD Setup

### Main Workflow File

```yaml
# .github/workflows/ci-cd.yml
name: EDMS CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Code Quality and Security
  code-quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install flake8 black isort bandit safety
        pip install -r backend/requirements/test.txt
    
    - name: Code formatting check
      run: |
        black --check backend/
        isort --check-only backend/
    
    - name: Linting
      run: flake8 backend/
    
    - name: Security scan
      run: |
        bandit -r backend/apps/
        safety check -r backend/requirements/production.txt
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Frontend linting
      run: |
        cd frontend
        npm run lint
        npm run type-check

  # Backend Testing
  backend-tests:
    runs-on: ubuntu-latest
    needs: code-quality
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: edms_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements/test.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=apps --cov-report=xml --cov-report=html
      env:
        DATABASE_URL: postgres://postgres:test_password@localhost:5432/edms_test
        REDIS_URL: redis://localhost:6379/0
        DJANGO_SETTINGS_MODULE: edms.settings.test
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend

  # Frontend Testing
  frontend-tests:
    runs-on: ubuntu-latest
    needs: code-quality
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info
        flags: frontend

  # E2E Testing
  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    if: github.event_name == 'pull_request'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Start services
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # Wait for services to start
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install Playwright
      run: |
        cd frontend
        npm ci
        npx playwright install
    
    - name: Run E2E tests
      run: |
        cd frontend
        npx playwright test
    
    - name: Upload test reports
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: playwright-report
        path: frontend/playwright-report/

  # Build Images
  build:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    strategy:
      matrix:
        component: [backend, frontend]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-${{ matrix.component }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./${{ matrix.component }}
        file: ./${{ matrix.component }}/Dockerfile.prod
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  # Deploy to Staging
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Add your staging deployment commands here

  # Deploy to Production
  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        # Add your production deployment commands here
```

## 5. Issue Templates

### Bug Report Template

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: Bug Report
description: Report a bug in the EDMS system
title: "[BUG] "
labels: ["bug", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report this bug!
        
  - type: input
    id: version
    attributes:
      label: Version
      description: What version of EDMS are you running?
      placeholder: e.g., v1.2.3
    validations:
      required: true
      
  - type: dropdown
    id: component
    attributes:
      label: Component
      description: Which component is affected?
      options:
        - Backend API
        - Frontend UI
        - Database
        - Authentication
        - Document Workflow
        - File Storage
        - Other
    validations:
      required: true
      
  - type: textarea
    id: description
    attributes:
      label: Bug Description
      description: A clear description of what the bug is
      placeholder: Tell us what you see!
    validations:
      required: true
      
  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      description: Steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Click on '....'
        3. Scroll down to '....'
        4. See error
    validations:
      required: true
      
  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What you expected to happen
    validations:
      required: true
      
  - type: textarea
    id: screenshots
    attributes:
      label: Screenshots
      description: Add screenshots to help explain your problem
      
  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: |
        Please provide details about your environment:
        - OS: [e.g. Ubuntu 20.04, Windows 10, macOS]
        - Browser: [e.g. Chrome 91, Firefox 89]
        - Python Version: [e.g. 3.11.0]
        - Node Version: [e.g. 18.17.0]
    validations:
      required: true
      
  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Add any other context about the problem here
```

### Feature Request Template

```yaml
# .github/ISSUE_TEMPLATE/feature_request.yml
name: Feature Request
description: Suggest a new feature for EDMS
title: "[FEATURE] "
labels: ["enhancement", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting a new feature!
        
  - type: dropdown
    id: component
    attributes:
      label: Component
      description: Which component would this feature affect?
      options:
        - Backend API
        - Frontend UI
        - Database
        - Authentication
        - Document Workflow
        - File Storage
        - Integration
        - Other
    validations:
      required: true
      
  - type: textarea
    id: problem
    attributes:
      label: Problem Description
      description: Is your feature request related to a problem? Please describe.
      placeholder: A clear description of what the problem is. Ex. I'm always frustrated when [...]
    validations:
      required: true
      
  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: Describe the solution you'd like
      placeholder: A clear description of what you want to happen.
    validations:
      required: true
      
  - type: textarea
    id: alternatives
    attributes:
      label: Alternative Solutions
      description: Describe alternatives you've considered
      placeholder: A clear description of any alternative solutions or features you've considered.
      
  - type: dropdown
    id: priority
    attributes:
      label: Priority
      description: How important is this feature?
      options:
        - Low
        - Medium
        - High
        - Critical
    validations:
      required: true
      
  - type: checkboxes
    id: compliance
    attributes:
      label: Compliance Impact
      description: Does this feature affect compliance requirements?
      options:
        - label: This feature affects 21 CFR Part 11 compliance
        - label: This feature affects audit trail requirements
        - label: This feature affects electronic signature validation
        - label: This feature affects data integrity
        
  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Add any other context or screenshots about the feature request here
```

## 6. GitHub Project Management Setup

### Create Project Board

```bash
# Using GitHub CLI to create project
gh project create --title "EDMS Development" --body "Track EDMS development progress"

# Add custom fields
gh project field-create --title "Priority" --type "single_select" --options "Low,Medium,High,Critical"
gh project field-create --title "Component" --type "single_select" --options "Backend,Frontend,Database,DevOps,Documentation"
gh project field-create --title "Sprint" --type "text"
gh project field-create --title "Story Points" --type "number"
```

### Project Views Setup

```markdown
# Create these views in your GitHub Project:

## 1. Sprint Planning View
- Group by: Sprint
- Filter: Status is "Todo" or "In Progress"
- Sort by: Priority (High to Low)

## 2. Component View
- Group by: Component
- Filter: All items
- Sort by: Status

## 3. Priority View
- Group by: Priority
- Filter: Status is not "Done"
- Sort by: Created date

## 4. Team View
- Group by: Assignee
- Filter: Status is "In Progress"
- Sort by: Due date
```

## 7. Repository Secrets and Variables

### Required Secrets

```bash
# Set up repository secrets via GitHub CLI or web interface
gh secret set DATABASE_PASSWORD --body "your-secure-database-password"
gh secret set DJANGO_SECRET_KEY --body "your-django-secret-key"
gh secret set JWT_SECRET_KEY --body "your-jwt-secret-key"
gh secret set AZURE_CLIENT_SECRET --body "your-azure-client-secret"
gh secret set EMAIL_HOST_PASSWORD --body "your-email-password"
gh secret set DOCKER_REGISTRY_TOKEN --body "your-registry-token"
gh secret set STAGING_KUBECONFIG --body "$(cat ~/.kube/staging-config | base64)"
gh secret set PRODUCTION_KUBECONFIG --body "$(cat ~/.kube/production-config | base64)"

# Repository variables
gh variable set ENVIRONMENT --body "production"
gh variable set REGISTRY_URL --body "ghcr.io"
gh variable set STAGING_URL --body "staging-edms.yourcompany.com"
gh variable set PRODUCTION_URL --body "edms.yourcompany.com"
```

## 8. Wiki and Documentation Setup

### Wiki Pages to Create

```markdown
# Create these pages in your GitHub Wiki:

## Home
- Project overview
- Quick links to documentation
- Getting started guide

## Development Setup
- Detailed setup instructions
- Troubleshooting guide
- Development best practices

## API Documentation
- API endpoint reference
- Authentication guide
- Example requests/responses

## Deployment Guide
- Environment setup
- Deployment procedures
- Rollback instructions

## Compliance Guide
- 21 CFR Part 11 requirements
- Audit trail procedures
- Validation protocols

## Architecture
- System architecture diagrams
- Database schema overview
- Integration points

## FAQ
- Common questions and answers
- Troubleshooting tips
- Known issues
```

## 9. Release Management

### Release Workflow

```bash
# Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0

# Update version numbers
# Update CHANGELOG.md
# Final testing

# Merge to main
git checkout main
git merge --no-ff release/v1.0.0

# Tag release
git tag -a v1.0.0 -m "Version 1.0.0: Initial release"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge --no-ff release/v1.0.0
git push origin develop

# Delete release branch
git branch -d release/v1.0.0
```

### CHANGELOG.md Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements

## [1.0.0] - 2024-02-01

### Added
- Initial release of EDMS system
- Document lifecycle management
- Electronic signature functionality
- User authentication and authorization
- Audit trail and compliance features
- RESTful API for document operations
- React-based user interface
- Elasticsearch integration for document search

### Security
- 21 CFR Part 11 compliance implementation
- Data encryption at rest and in transit
- Multi-factor authentication support
- Role-based access control
```

## Next Steps

1. **Create the repository** on GitHub using the provided templates
2. **Set up branch protection** rules for main and develop branches
3. **Configure GitHub Actions** for automated testing and deployment
4. **Create issue templates** for bug reports and feature requests
5. **Set up project board** for tracking development progress
6. **Configure repository secrets** for CI/CD pipeline
7. **Create initial wiki pages** for documentation
8. **Invite team members** and assign appropriate permissions

Your EDMS repository is now ready for collaborative development with proper project management and CI/CD automation! 🚀