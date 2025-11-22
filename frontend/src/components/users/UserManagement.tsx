import React, { useState, useCallback } from 'react';
import { User, Role } from '../../types/api';

interface UserManagementProps {
  className?: string;
}

interface UserWithRoles extends User {
  assigned_roles: Role[];
}

const UserManagement: React.FC<UserManagementProps> = ({ className = '' }) => {
  const [users, setUsers] = useState<UserWithRoles[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<UserWithRoles | null>(null);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);

  // Mock users data
  const mockUsers: UserWithRoles[] = [
    {
      id: 1,
      username: 'admin',
      email: 'admin@edms.local',
      first_name: 'System',
      last_name: 'Administrator',
      is_active: true,
      is_staff: true,
      is_superuser: true,
      date_joined: '2024-01-01T00:00:00Z',
      last_login: '2024-11-22T02:30:00Z',
      full_name: 'System Administrator',
      roles: [],
      assigned_roles: [
        {
          id: 1,
          name: 'System Administrator',
          description: 'Full system access',
          module: 'system',
          permission_level: 'admin',
          permissions: ['all']
        }
      ]
    },
    {
      id: 2,
      username: 'author',
      email: 'author@edms.local',
      first_name: 'Document',
      last_name: 'Author',
      is_active: true,
      is_staff: false,
      is_superuser: false,
      date_joined: '2024-01-15T00:00:00Z',
      last_login: '2024-11-21T08:00:00Z',
      full_name: 'Document Author',
      roles: [],
      assigned_roles: [
        {
          id: 2,
          name: 'Document Author',
          description: 'Can create and edit documents',
          module: 'documents',
          permission_level: 'write',
          permissions: ['document.create', 'document.edit']
        }
      ]
    },
    {
      id: 3,
      username: 'reviewer',
      email: 'reviewer@edms.local',
      first_name: 'Document',
      last_name: 'Reviewer',
      is_active: true,
      is_staff: false,
      is_superuser: false,
      date_joined: '2024-01-20T00:00:00Z',
      last_login: '2024-11-21T10:00:00Z',
      full_name: 'Document Reviewer',
      roles: [],
      assigned_roles: [
        {
          id: 3,
          name: 'Document Reviewer',
          description: 'Can review and approve documents',
          module: 'documents',
          permission_level: 'review',
          permissions: ['document.read', 'document.review']
        }
      ]
    },
    {
      id: 4,
      username: 'approver',
      email: 'approver@edms.local',
      first_name: 'Document',
      last_name: 'Approver',
      is_active: true,
      is_staff: false,
      is_superuser: false,
      date_joined: '2024-01-25T00:00:00Z',
      last_login: '2024-11-20T16:00:00Z',
      full_name: 'Document Approver',
      roles: [],
      assigned_roles: [
        {
          id: 4,
          name: 'Document Approver',
          description: 'Can approve and finalize documents',
          module: 'documents',
          permission_level: 'approve',
          permissions: ['document.read', 'document.review', 'document.approve']
        }
      ]
    }
  ];

  React.useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setUsers(mockUsers);
      setLoading(false);
    }, 1000);
  }, []);

  const handleCreateUser = useCallback(() => {
    setSelectedUser(null);
    setShowCreateUser(true);
  }, []);

  const handleEditUser = useCallback((user: UserWithRoles) => {
    setSelectedUser(user);
    setShowEditUser(true);
  }, []);

  const handleDeactivateUser = useCallback((user: UserWithRoles) => {
    if (window.confirm(`Are you sure you want to deactivate ${user.full_name}?`)) {
      // TODO: Implement user deactivation
      alert(`User ${user.full_name} deactivation will be implemented in the backend integration phase.`);
    }
  }, []);

  const getRoleColor = (permissionLevel: string): string => {
    const colors: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      approve: 'bg-purple-100 text-purple-800',
      review: 'bg-blue-100 text-blue-800',
      write: 'bg-green-100 text-green-800',
      read: 'bg-gray-100 text-gray-800'
    };
    return colors[permissionLevel] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">User Management</h3>
            <p className="text-sm text-gray-500">
              Manage user accounts, roles, and permissions
            </p>
          </div>
          <button
            onClick={handleCreateUser}
            className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Add User
          </button>
        </div>

        {/* Users List */}
        <div className="space-y-4">
          {users.map((user) => (
            <div
              key={user.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                    <span className="text-lg font-medium text-gray-600">
                      {user.first_name[0]}{user.last_name[0]}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      {user.full_name}
                    </h4>
                    <p className="text-sm text-gray-500">{user.email}</p>
                    <p className="text-xs text-gray-400">@{user.username}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {/* Roles */}
                  <div className="flex flex-wrap gap-1">
                    {user.assigned_roles.map((role) => (
                      <span
                        key={role.id}
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(role.permission_level)}`}
                      >
                        {role.name}
                      </span>
                    ))}
                  </div>

                  {/* Status */}
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {user.is_superuser && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Super Admin
                      </span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEditUser(user)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    {user.is_active && !user.is_superuser && (
                      <button
                        onClick={() => handleDeactivateUser(user)}
                        className="text-sm text-red-600 hover:text-red-800"
                      >
                        Deactivate
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div className="mt-3 text-xs text-gray-500 flex items-center space-x-4">
                <span>Joined: {formatDate(user.date_joined)}</span>
                {user.last_login && (
                  <span>Last login: {formatDate(user.last_login)}</span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Modals */}
        {(showCreateUser || showEditUser) && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                {showCreateUser ? 'Create New User' : 'Edit User'}
              </h4>
              <p className="text-gray-600 mb-4">
                User management forms will be implemented in the next iteration.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreateUser(false);
                    setShowEditUser(false);
                    setSelectedUser(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;