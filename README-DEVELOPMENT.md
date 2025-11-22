# EDMS Development Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local frontend development)

### 1. Initial Setup
```bash
# Clone and enter the repository
git clone <repository-url>
cd edms

# Make scripts executable
chmod +x scripts/*.sh

# Start development environment (first time)
./scripts/start-development.sh --init
```

### 2. Create Test Users
```bash
# After initial setup, create test users
./scripts/create-test-users.sh
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/v1/docs/

## 📁 Project Structure

```
edms/
├── backend/                    # Django application
│   ├── edms/                  # Django project settings
│   ├── apps/                  # Django apps
│   │   ├── users/            # User Management (S1)
│   │   ├── documents/        # Document Management (O1)
│   │   ├── workflows/        # Workflow Engine
│   │   ├── audit/           # Audit Trail (S2)
│   │   ├── placeholders/    # Placeholder Management (S6)
│   │   ├── scheduler/       # Scheduler (S3)
│   │   ├── backup/         # Backup & Health Check (S4)
│   │   └── settings/       # App Settings (S7)
│   └── requirements/       # Python dependencies
├── frontend/               # React application
│   ├── src/               # Source code
│   └── public/            # Static assets
├── infrastructure/        # Container configurations
├── scripts/              # Development scripts
├── storage/             # Document storage (created at runtime)
└── Dev_Docs/           # Technical documentation
```

## 🛠️ Development Commands

### Backend Commands
```bash
# Run Django commands
docker-compose exec backend python manage.py <command>

# Database migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run tests
docker-compose exec backend pytest

# Django shell
docker-compose exec backend python manage.py shell
```

### Frontend Commands
```bash
# Install dependencies
cd frontend && npm install

# Start development server
cd frontend && npm start

# Run tests
cd frontend && npm test

# Build for production
cd frontend && npm run build
```

### Container Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Rebuild containers
docker-compose build

# Reset everything (⚠️ DESTRUCTIVE)
docker-compose down -v && docker system prune -f
```

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=apps

# Run specific test
docker-compose exec backend pytest apps/users/tests.py
```

### Frontend Testing
```bash
# Unit tests
cd frontend && npm test

# E2E tests
cd frontend && npm run test:e2e
```

## 🔧 Configuration

### Environment Variables
Copy `backend/.env.example` to `backend/.env` and customize:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=edms_db
DB_USER=edms_user
DB_PASSWORD=edms_password
```

### Test Users
Default test accounts (created by `create-test-users.sh`):

- **Document Admin**: `docadmin` / `EDMSAdmin2024!`
- **Document Author**: `author` / `AuthorPass2024!`
- **Document Reviewer**: `reviewer` / `ReviewPass2024!`
- **Document Approver**: `approver` / `ApprovePass2024!`
- **Placeholder Admin**: `placeholderadmin` / `PlaceholderAdmin2024!`

## 📊 Development Status

### ✅ Completed
- Project structure and documentation
- Django backend foundation
- User management system (S1)
- Docker containerization
- Development environment setup
- Basic React frontend structure

### 🏗️ In Progress
- Document management models (O1)
- Workflow engine integration
- Audit trail implementation (S2)
- API endpoints and serializers

### ⏳ Planned
- Document processing pipeline
- Placeholder replacement system (S6)
- Frontend components and pages
- Authentication integration
- Testing framework implementation

## 🚨 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Reset database
docker-compose down -v
docker-compose up -d db
sleep 10
docker-compose exec backend python manage.py migrate
```

**Frontend Dependencies Issue**
```bash
# Clean install
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Container Build Issues**
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Logs and Debugging
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Check container status
docker-compose ps
```

## 📚 Next Steps

1. **Implement Document Models**: Complete the document management models in `apps/documents/`
2. **Add Workflow Engine**: Integrate Enhanced Simple Workflow Engine for workflow management
3. **Build API Endpoints**: Implement REST API endpoints for all modules
4. **Create Frontend Components**: Build React components for document management
5. **Add Authentication**: Implement JWT authentication and user management
6. **Testing**: Add comprehensive test coverage

## 🤝 Contributing

1. Read the main `README.md` and `CONTRIBUTING.md`
2. Check `AGENTS.md` for development guidelines
3. Follow the established patterns in the codebase
4. Ensure all tests pass before submitting PRs
5. Update documentation as needed

For detailed technical specifications, see the `Dev_Docs/` directory.