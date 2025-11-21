# Frontend Component Specifications

## Overview
This document provides comprehensive React frontend component specifications for the EDMS system, including component architecture, state management, routing, and UI/UX design patterns.

## Technology Stack

```json
{
  "framework": "React 18",
  "styling": "Tailwind CSS 3.x",
  "state_management": "Redux Toolkit + RTK Query",
  "routing": "React Router v6",
  "forms": "React Hook Form + Yup",
  "ui_components": "Headless UI + Custom Components",
  "icons": "Heroicons",
  "date_handling": "date-fns",
  "file_handling": "react-dropzone",
  "notifications": "react-hot-toast",
  "charts": "Chart.js + react-chartjs-2"
}
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/           # Reusable UI components
│   │   ├── documents/        # Document-specific components
│   │   ├── users/            # User management components
│   │   ├── workflow/         # Workflow components
│   │   ├── auth/             # Authentication components
│   │   ├── audit/            # Audit trail components
│   │   ├── settings/         # Settings components
│   │   └── layout/           # Layout components
│   ├── pages/                # Page components
│   ├── hooks/                # Custom hooks
│   ├── services/             # API services
│   ├── store/                # Redux store
│   ├── utils/                # Utility functions
│   ├── contexts/             # React contexts
│   ├── types/                # TypeScript types
│   └── constants/            # Application constants
├── public/
└── tests/
```

## Core Layout Components

### Main Layout

```tsx
// src/components/layout/MainLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';
import { BreadcrumbNavigation } from './BreadcrumbNavigation';
import { useAuth } from '../../hooks/useAuth';

export const MainLayout: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header user={user} />
        <BreadcrumbNavigation />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
        <Footer />
      </div>
    </div>
  );
};
```

### Header Component

```tsx
// src/components/layout/Header.tsx
import React, { useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { BellIcon, UserCircleIcon, CogIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../hooks/useAuth';
import { NotificationDropdown } from '../common/NotificationDropdown';

interface HeaderProps {
  user: User;
}

export const Header: React.FC<HeaderProps> = ({ user }) => {
  const { logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center">
          <h1 className="text-xl font-semibold text-gray-900">
            Electronic Document Management System
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="hidden md:block">
            <div className="relative">
              <input
                type="text"
                placeholder="Search documents..."
                className="w-64 px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 text-gray-500 hover:text-gray-700 relative"
            >
              <BellIcon className="h-6 w-6" />
              <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white" />
            </button>
            {showNotifications && (
              <NotificationDropdown onClose={() => setShowNotifications(false)} />
            )}
          </div>

          {/* User Menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center space-x-2 p-2 text-gray-700 hover:text-gray-900">
              <UserCircleIcon className="h-8 w-8" />
              <span className="text-sm font-medium">{user.first_name} {user.last_name}</span>
            </Menu.Button>

            <Transition
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none">
                <Menu.Item>
                  <a href="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    Your Profile
                  </a>
                </Menu.Item>
                <Menu.Item>
                  <a href="/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    Settings
                  </a>
                </Menu.Item>
                <Menu.Item>
                  <button
                    onClick={logout}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Sign out
                  </button>
                </Menu.Item>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </header>
  );
};
```

### Sidebar Navigation

```tsx
// src/components/layout/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  DocumentIcon,
  UsersIcon,
  CogIcon,
  ChartBarIcon,
  ClipboardDocumentListIcon,
  ArchiveBoxIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../hooks/useAuth';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ForwardRefExoticComponent<any>;
  permission?: string;
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: ChartBarIcon },
  { name: 'Documents', href: '/documents', icon: DocumentIcon },
  { name: 'Workflow', href: '/workflow', icon: ClipboardDocumentListIcon },
  { name: 'Archive', href: '/archive', icon: ArchiveBoxIcon },
  { name: 'Users', href: '/users', icon: UsersIcon, permission: 'user_management' },
  { name: 'Audit Trail', href: '/audit', icon: ClipboardDocumentListIcon, permission: 'audit_access' },
  { name: 'Settings', href: '/settings', icon: CogIcon, permission: 'admin_access' },
];

export const Sidebar: React.FC = () => {
  const { user, hasPermission } = useAuth();

  const filteredNavigation = navigation.filter(item => 
    !item.permission || hasPermission(item.permission)
  );

  return (
    <div className="w-64 bg-gray-900 text-white flex-shrink-0">
      <div className="p-6">
        <h2 className="text-lg font-semibold">EDMS</h2>
      </div>
      
      <nav className="mt-8">
        <div className="space-y-1">
          {filteredNavigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center px-6 py-3 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-gray-800 text-white border-r-2 border-blue-500'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`
              }
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="absolute bottom-0 w-64 p-6 border-t border-gray-700">
        <div className="flex items-center">
          <div className="ml-3">
            <p className="text-sm font-medium">{user?.first_name} {user?.last_name}</p>
            <p className="text-xs text-gray-400">{user?.profile?.department}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
```

## Document Components

### Document List Component

```tsx
// src/components/documents/DocumentList.tsx
import React, { useState } from 'react';
import { useQuery } from '@reduxjs/toolkit/query/react';
import { documentsApi } from '../../services/documentsApi';
import { DocumentCard } from './DocumentCard';
import { DocumentFilters } from './DocumentFilters';
import { DocumentSearch } from './DocumentSearch';
import { Pagination } from '../common/Pagination';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { EmptyState } from '../common/EmptyState';

export const DocumentList: React.FC = () => {
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 20,
    search: '',
    status: '',
    document_type: '',
    author: '',
  });

  const {
    data: documentsData,
    isLoading,
    error,
  } = useQuery(documentsApi.endpoints.getDocuments.initiate(filters));

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading documents</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <button
          onClick={() => navigate('/documents/create')}
          className="btn-primary"
        >
          Create Document
        </button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <DocumentSearch
          value={filters.search}
          onChange={(search) => setFilters({ ...filters, search, page: 1 })}
        />
        <DocumentFilters
          filters={filters}
          onChange={setFilters}
        />
      </div>

      {documentsData?.results.length === 0 ? (
        <EmptyState
          title="No documents found"
          description="Create your first document to get started."
          actionLabel="Create Document"
          onAction={() => navigate('/documents/create')}
        />
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {documentsData?.results.map((document) => (
              <DocumentCard
                key={document.id}
                document={document}
              />
            ))}
          </div>

          <Pagination
            currentPage={filters.page}
            totalPages={Math.ceil(documentsData.count / filters.page_size)}
            onPageChange={(page) => setFilters({ ...filters, page })}
          />
        </>
      )}
    </div>
  );
};
```

### Document Card Component

```tsx
// src/components/documents/DocumentCard.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import {
  DocumentTextIcon,
  EyeIcon,
  PencilIcon,
  DownloadIcon,
} from '@heroicons/react/24/outline';
import { Document } from '../../types/document';
import { StatusBadge } from '../common/StatusBadge';
import { ActionsDropdown } from '../common/ActionsDropdown';

interface DocumentCardProps {
  document: Document;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document }) => {
  const actions = [
    {
      label: 'View',
      icon: EyeIcon,
      onClick: () => navigate(`/documents/${document.id}`),
    },
    {
      label: 'Edit',
      icon: PencilIcon,
      onClick: () => navigate(`/documents/${document.id}/edit`),
      disabled: !document.can_edit,
    },
    {
      label: 'Download',
      icon: DownloadIcon,
      onClick: () => handleDownload(document.id, 'original'),
      disabled: !document.can_download,
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200">
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center">
            <DocumentTextIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-3">
              <Link
                to={`/documents/${document.id}`}
                className="font-medium text-gray-900 hover:text-blue-600"
              >
                {document.title}
              </Link>
              <p className="text-sm text-gray-500">{document.document_number}</p>
            </div>
          </div>
          <ActionsDropdown actions={actions} />
        </div>

        <div className="mt-4">
          <StatusBadge status={document.status} />
        </div>

        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Version:</span>
            <span className="font-medium">{document.version}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Type:</span>
            <span>{document.document_type.name}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Author:</span>
            <span>{document.author.first_name} {document.author.last_name}</span>
          </div>
          {document.effective_date && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Effective:</span>
              <span>{format(new Date(document.effective_date), 'MMM dd, yyyy')}</span>
            </div>
          )}
        </div>

        {document.description && (
          <p className="mt-4 text-sm text-gray-600 line-clamp-2">
            {document.description}
          </p>
        )}
      </div>
    </div>
  );
};
```

### Document Creation Form

```tsx
// src/components/documents/DocumentForm.tsx
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useDropzone } from 'react-dropzone';
import { FormField } from '../common/FormField';
import { Select } from '../common/Select';
import { FileUpload } from '../common/FileUpload';
import { Button } from '../common/Button';

const schema = yup.object({
  title: yup.string().required('Title is required').max(255),
  description: yup.string().max(1000),
  document_type_id: yup.number().required('Document type is required'),
  document_source_id: yup.number().required('Document source is required'),
  dependencies: yup.array().of(yup.string()),
  file: yup.mixed().required('File is required'),
});

interface DocumentFormProps {
  onSubmit: (data: DocumentFormData) => void;
  isLoading?: boolean;
  initialData?: Partial<DocumentFormData>;
}

export const DocumentForm: React.FC<DocumentFormProps> = ({
  onSubmit,
  isLoading = false,
  initialData,
}) => {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
    setValue,
    watch,
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: initialData,
  });

  const { data: documentTypes } = useQuery(documentsApi.endpoints.getDocumentTypes.initiate());
  const { data: documentSources } = useQuery(documentsApi.endpoints.getDocumentSources.initiate());

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-6">Document Information</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            label="Title"
            error={errors.title?.message}
            required
          >
            <input
              {...register('title')}
              className="form-input"
              placeholder="Enter document title"
            />
          </FormField>

          <Controller
            name="document_type_id"
            control={control}
            render={({ field }) => (
              <FormField
                label="Document Type"
                error={errors.document_type_id?.message}
                required
              >
                <Select
                  {...field}
                  options={documentTypes?.map(type => ({
                    value: type.id,
                    label: type.name,
                  })) || []}
                  placeholder="Select document type"
                />
              </FormField>
            )}
          />

          <Controller
            name="document_source_id"
            control={control}
            render={({ field }) => (
              <FormField
                label="Document Source"
                error={errors.document_source_id?.message}
                required
              >
                <Select
                  {...field}
                  options={documentSources?.map(source => ({
                    value: source.id,
                    label: source.name,
                  })) || []}
                  placeholder="Select document source"
                />
              </FormField>
            )}
          />

          <div className="md:col-span-2">
            <FormField
              label="Description"
              error={errors.description?.message}
            >
              <textarea
                {...register('description')}
                rows={4}
                className="form-textarea"
                placeholder="Enter document description"
              />
            </FormField>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-6">File Upload</h3>
        
        <Controller
          name="file"
          control={control}
          render={({ field }) => (
            <FileUpload
              {...field}
              accept={{
                'application/pdf': ['.pdf'],
                'application/msword': ['.doc'],
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
              }}
              maxSize={100 * 1024 * 1024} // 100MB
              error={errors.file?.message}
            />
          )}
        />
      </div>

      <div className="flex justify-end space-x-4">
        <Button
          type="button"
          variant="secondary"
          onClick={() => navigate(-1)}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          loading={isLoading}
        >
          Create Document
        </Button>
      </div>
    </form>
  );
};
```

## Workflow Components

### Workflow Status Component

```tsx
// src/components/workflow/WorkflowStatus.tsx
import React from 'react';
import { CheckCircleIcon, ClockIcon, XCircleIcon } from '@heroicons/react/24/solid';
import { Document } from '../../types/document';

interface WorkflowStep {
  id: string;
  title: string;
  status: 'completed' | 'current' | 'upcoming' | 'rejected';
  user?: string;
  date?: string;
  comments?: string;
}

interface WorkflowStatusProps {
  document: Document;
}

export const WorkflowStatus: React.FC<WorkflowStatusProps> = ({ document }) => {
  const getWorkflowSteps = (): WorkflowStep[] => {
    const steps: WorkflowStep[] = [
      {
        id: 'draft',
        title: 'Draft Created',
        status: 'completed',
        user: document.author.first_name + ' ' + document.author.last_name,
        date: document.created_at,
      },
    ];

    // Add steps based on document status
    if (document.status !== 'draft') {
      steps.push({
        id: 'review',
        title: 'Review',
        status: ['pending_review', 'reviewed'].includes(document.status) ? 'current' : 
                document.status === 'draft' ? 'upcoming' : 'completed',
        user: document.reviewer?.first_name + ' ' + document.reviewer?.last_name,
      });
    }

    if (['reviewed', 'pending_approval', 'approved_pending_effective', 'approved_effective'].includes(document.status)) {
      steps.push({
        id: 'approval',
        title: 'Approval',
        status: document.status === 'pending_approval' ? 'current' : 
                ['reviewed'].includes(document.status) ? 'upcoming' : 'completed',
        user: document.approver?.first_name + ' ' + document.approver?.last_name,
        date: document.approval_date,
      });
    }

    if (['approved_pending_effective', 'approved_effective'].includes(document.status)) {
      steps.push({
        id: 'effective',
        title: 'Effective',
        status: document.status === 'approved_effective' ? 'completed' : 'upcoming',
        date: document.effective_date,
      });
    }

    return steps;
  };

  const steps = getWorkflowSteps();

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-6">Workflow Status</h3>
      
      <div className="flow-root">
        <ul className="-mb-8">
          {steps.map((step, stepIdx) => (
            <li key={step.id}>
              <div className="relative pb-8">
                {stepIdx !== steps.length - 1 ? (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                ) : null}
                <div className="relative flex space-x-3">
                  <div>
                    {step.status === 'completed' ? (
                      <CheckCircleIcon className="h-8 w-8 text-green-500" />
                    ) : step.status === 'current' ? (
                      <ClockIcon className="h-8 w-8 text-yellow-500" />
                    ) : step.status === 'rejected' ? (
                      <XCircleIcon className="h-8 w-8 text-red-500" />
                    ) : (
                      <div className="h-8 w-8 bg-gray-300 rounded-full flex items-center justify-center">
                        <div className="h-2 w-2 bg-gray-500 rounded-full" />
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{step.title}</p>
                      {step.user && (
                        <p className="text-sm text-gray-500">{step.user}</p>
                      )}
                      {step.date && (
                        <p className="text-sm text-gray-500">
                          {format(new Date(step.date), 'MMM dd, yyyy')}
                        </p>
                      )}
                    </div>
                    {step.comments && (
                      <div className="mt-2">
                        <p className="text-sm text-gray-600">{step.comments}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
```

## Common UI Components

### Button Component

```tsx
// src/components/common/Button.tsx
import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors';
  
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
  };

  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const classes = `
    ${baseClasses}
    ${variants[variant]}
    ${sizes[size]}
    ${(disabled || loading) ? 'opacity-50 cursor-not-allowed' : ''}
    ${className}
  `.trim();

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <LoadingSpinner size="sm" className="mr-2" />}
      {icon && !loading && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};
```

This frontend specification provides:

1. **Complete component architecture** with proper TypeScript types
2. **Responsive design** using Tailwind CSS
3. **State management** with Redux Toolkit
4. **Form handling** with React Hook Form and validation
5. **Accessibility features** with Headless UI components
6. **Reusable UI components** following design system principles
7. **Document management interface** with workflow visualization
8. **User authentication and authorization** integration
9. **File upload and management** capabilities
10. **Professional UI/UX design** suitable for enterprise use

The components are designed to work seamlessly with the backend API specifications and provide a modern, responsive user experience.