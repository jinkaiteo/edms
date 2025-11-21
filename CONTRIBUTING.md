# Contributing to EDMS

Thank you for your interest in contributing to the Electronic Document Management System! This document provides guidelines and information for contributors.

## 🎯 Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Podman or Docker
- Git knowledge
- Understanding of Django and React

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/jinkaiteo/edms.git
   cd edms
   ```

2. **Set up Development Environment**
   ```bash
   bash scripts/infrastructure-setup.sh
   bash scripts/start-development.sh --init
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📋 Development Guidelines

### 🏗️ Architecture Principles
- **21 CFR Part 11 Compliance**: All changes must maintain regulatory compliance
- **ALCOA Principles**: Ensure data integrity in all modifications
- **Security First**: Security considerations in every pull request
- **Modularity**: Keep code modular and well-organized
- **Documentation**: Document all public APIs and complex logic

### 🐍 Backend (Django) Standards

#### Code Style
- Follow **PEP 8** style guidelines
- Use **Black** for code formatting: `black .`
- Use **isort** for import sorting: `isort .`
- Use **flake8** for linting: `flake8 .`

#### Django Conventions
- Use Django's class-based views where appropriate
- Follow Django REST Framework patterns for APIs
- Use Django-River for workflow management
- Implement proper model validation and clean methods

#### Example Structure
```python
# apps/documents/models.py
from django.db import models
from django.core.validators import FileExtensionValidator
from django_river.models import State

class Document(models.Model):
    """
    Core document model with 21 CFR Part 11 compliance features.
    """
    title = models.CharField(max_length=500, help_text="Document title")
    
    class Meta:
        db_table = 'edms_documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    def clean(self):
        """Validate document data for compliance."""
        super().clean()
        # Validation logic here
    
    def save(self, *args, **kwargs):
        """Override save to add audit trail."""
        super().save(*args, **kwargs)
        # Audit logging here
```

### ⚛️ Frontend (React) Standards

#### Code Style
- Use **TypeScript** for type safety
- Follow **ESLint** and **Prettier** configurations
- Use **functional components** with hooks
- Implement **proper error boundaries**

#### React Conventions
- Use **Redux Toolkit** for state management
- Implement **React Query** for API calls
- Use **Tailwind CSS** for styling
- Follow **accessibility guidelines** (WCAG 2.1)

#### Example Structure
```typescript
// src/components/documents/DocumentUpload.tsx
import React, { useState } from 'react';
import { useAppDispatch } from '../../store/hooks';
import { uploadDocument } from '../../store/slices/documentsSlice';

interface DocumentUploadProps {
  onSuccess: (documentId: string) => void;
  allowedTypes: string[];
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onSuccess,
  allowedTypes
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const dispatch = useAppDispatch();

  // Component logic here

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      {/* Component JSX here */}
    </div>
  );
};
```

### 🧪 Testing Requirements

#### Backend Testing
- **Unit Tests**: Test all models, views, and services
- **Integration Tests**: Test API endpoints
- **Compliance Tests**: Verify 21 CFR Part 11 requirements

```python
# tests/test_documents.py
import pytest
from django.test import TestCase
from apps.documents.models import Document

class DocumentModelTest(TestCase):
    def test_document_creation(self):
        """Test document creation with valid data."""
        document = Document.objects.create(
            title="Test Document",
            document_type="SOP"
        )
        self.assertEqual(document.status, "DRAFT")
        self.assertIsNotNone(document.created_at)
```

#### Frontend Testing
- **Unit Tests**: Test individual components
- **Integration Tests**: Test user workflows
- **E2E Tests**: Test complete user journeys

```typescript
// src/components/__tests__/DocumentUpload.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentUpload } from '../DocumentUpload';

describe('DocumentUpload', () => {
  test('renders upload form correctly', () => {
    render(<DocumentUpload onSuccess={jest.fn()} allowedTypes={['.pdf']} />);
    expect(screen.getByText('Upload Document')).toBeInTheDocument();
  });
});
```

## 🔄 Pull Request Process

### 1. Before Creating PR
- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] Compliance requirements are met
- [ ] Security review completed

### 2. PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Compliance enhancement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Compliance Checklist
- [ ] 21 CFR Part 11 requirements maintained
- [ ] Audit trail functionality preserved
- [ ] Security implications reviewed

## Screenshots (if applicable)
[Add screenshots for UI changes]
```

### 3. Review Process
1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: At least one maintainer reviews
3. **Security Review**: Security-critical changes require additional review
4. **Compliance Review**: Regulatory changes require compliance review
5. **Testing**: All tests must pass
6. **Approval**: Maintainer approval required

### 4. Merge Requirements
- [ ] All reviews approved
- [ ] All CI checks passing
- [ ] Branch up to date with main
- [ ] No merge conflicts

## 🎯 Issue Guidelines

### Bug Reports
```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to...
2. Click on...
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Browser: [e.g., Chrome 91]
- Version: [e.g., v1.0.0]

**Additional Context**
Any other context about the problem.
```

### Feature Requests
```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Why this feature would be valuable.

**Proposed Solution**
How you envision this working.

**Compliance Impact**
Any 21 CFR Part 11 implications.

**Alternatives Considered**
Other solutions you've considered.
```

## 🏷️ Branching Strategy

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Workflow
```
main (production)
├── develop (integration)
    ├── feature/document-upload
    ├── feature/workflow-notifications
    └── bugfix/audit-trail-fix
```

## 🚀 Release Process

1. **Feature Freeze**: Stop accepting new features
2. **Testing Phase**: Comprehensive testing
3. **Release Candidate**: Create RC branch
4. **Final Testing**: Production-like environment testing
5. **Release**: Merge to main and tag
6. **Post-Release**: Monitor and hotfix if needed

## 📚 Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://reactjs.org/docs/)
- [21 CFR Part 11 Guide](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)

### Development Tools
- [Django Extensions](https://django-extensions.readthedocs.io/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Developer Tools](https://reactjs.org/blog/2019/08/15/new-react-devtools.html)

### Testing Tools
- [pytest](https://docs.pytest.org/)
- [Jest](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

## 🤝 Community

### Communication Channels
- **GitHub Discussions**: General questions and discussions
- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions

### Getting Help
- Check existing [Issues](https://github.com/jinkaiteo/edms/issues)
- Search [Discussions](https://github.com/jinkaiteo/edms/discussions)
- Review [Documentation](Dev_Docs/)

## 🎉 Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Annual contributor recognition

Thank you for contributing to EDMS! Together, we're building a robust, compliant document management system. 🚀
