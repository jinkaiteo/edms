# EDMS - Electronic Document Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/react-18+-61DAFB.svg)](https://reactjs.org/)

## 🎯 Overview

A **21 CFR Part 11 compliant** Electronic Document Management System designed for regulated industries like pharmaceuticals. Built with Django, React, and containerized with Podman for secure, on-premise deployment.

## ✨ Key Features

- **📋 Complete Document Lifecycle Management**
- **🔄 Dynamic Workflow Engine** (Draft → Review → Approval → Effective)
- **📝 Electronic Signatures** with full audit trail
- **🔐 Role-Based Access Control** and user management
- **🔍 Full-Text Search** with Elasticsearch
- **📊 Compliance Dashboard** and reporting
- **🔒 End-to-End Encryption** for sensitive documents
- **⚡ Real-time Notifications** and task management

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 4.2 + Django REST Framework + Django-River
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Database**: PostgreSQL 18 with encryption
- **Cache**: Redis for sessions and task queue
- **Search**: Elasticsearch for document indexing
- **Containers**: Podman/Docker with multi-container deployment
- **Authentication**: Entra ID integration support

### System Modules
- **O1 - Electronic Document Management**: Core document lifecycle
- **S1 - User Management**: Role-based access control
- **S2 - Audit Trail**: Complete compliance tracking
- **S3 - Scheduler**: Automated workflows and tasks
- **S4 - Backup & Health Check**: System monitoring
- **S5 - Workflow Settings**: Dynamic workflow configuration
- **S6 - Placeholder Management**: Document templates
- **S7 - App Settings**: System configuration

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Podman or Docker
- PostgreSQL 18
- Redis 7+
- Elasticsearch 8.11+

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/edms-system.git
cd edms-system

# Run setup script
bash scripts/infrastructure-setup.sh

# Start development environment
bash scripts/start-development.sh --init
```

### Docker Setup

```bash
# Start all services
podman-compose up -d

# Initialize database
bash scripts/initialize-database.sh

# Create test users
bash scripts/create-test-users.sh
```

## 📁 Project Structure

```
edms-system/
├── backend/                # Django application
│   ├── edms/              # Django project
│   ├── apps/              # Django apps (documents, users, workflows)
│   └── requirements/      # Python dependencies
├── frontend/              # React application
│   ├── src/              # React components and pages
│   └── public/           # Static assets
├── infrastructure/        # Container and deployment configs
│   ├── containers/       # Container configurations
│   ├── nginx/           # Nginx configurations
│   └── monitoring/      # Monitoring setup
├── scripts/              # Automation scripts
├── Dev_Docs/            # Complete technical documentation
└── storage/             # Document storage (encrypted)
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=apps

# Frontend tests
cd frontend
npm test

# End-to-end tests
npx playwright test
```

## 🏭 Production Deployment

The system supports multiple deployment options:
- **Container orchestration** with Podman/Docker Compose
- **Kubernetes** deployment with Helm charts
- **CI/CD pipeline** with GitHub Actions

See [Deployment Guide](Dev_Docs/Deployment_Configurations.md) for detailed instructions.

## 📋 Compliance Features

### 21 CFR Part 11 Support
- ✅ **Electronic Records** with complete metadata
- ✅ **Electronic Signatures** with validation
- ✅ **Audit Trail** with tamper-proof logging
- ✅ **Access Controls** with role-based permissions
- ✅ **System Validation** documentation
- ✅ **Data Integrity** with checksums and encryption

### ALCOA Principles
- **Attributable**: All actions linked to users
- **Legible**: Clear, readable audit trails
- **Contemporaneous**: Real-time activity logging
- **Original**: Tamper-proof record keeping
- **Accurate**: Data validation and integrity checks

## 📚 Documentation

- **[Complete Technical Specs](Dev_Docs/)** - Detailed system documentation
- **[API Documentation](Dev_Docs/2_EDMS_API_Specifications.md)** - REST API reference
- **[Database Schema](Dev_Docs/1_EDMS_Database_Schema_Complete.md)** - Complete database design
- **[Workflow Setup](Dev_Docs/3_Django_River_Workflow_Setup.md)** - Workflow configuration
- **[Security Guide](Dev_Docs/4_Authentication_Integration.md)** - Security implementation

## 📊 Project Status

- ✅ **Architecture and design complete**
- ✅ **Development documentation ready**
- ✅ **HTTP-only deployment configured**
- 🏗️ **Core backend development in progress**
- ⏳ **Frontend development starting**
- ⏳ **Testing framework implementation**
- ⏳ **CI/CD pipeline setup**

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:
- Code of conduct
- Development process
- Pull request procedure
- Coding standards

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛡️ Security

For security concerns, please review our [Security Policy](SECURITY.md).

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/your-username/edms-system/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/edms-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/edms-system/discussions)

---

**Built with ❤️ for regulated industries requiring compliant document management.**