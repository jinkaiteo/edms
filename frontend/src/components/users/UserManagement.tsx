import React, { useState, useCallback, useEffect } from 'react';
import { User, Role } from '../../types/api';
import apiService from '../../services/api.ts';

interface UserManagementProps {
  className?: string;
}

interface UserWithRoles extends User {
  active_roles: Role[];
}

interface CreateUserFormData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  employee_id: string;
  phone_number: string;
  department: string;
  position: string;
  role_id?: number;
}

interface EditUserFormData {
  email: string;
  first_name: string;
  last_name: string;
  employee_id: string;
  phone_number: string;
  department: string;
  position: string;
  is_active: boolean;
}

interface PasswordResetFormData {
  new_password: string;
  new_password_confirm: string;
  reason: string;
}

const UserManagement: React.FC<UserManagementProps> = ({ className = '' }) => {
  const [users, setUsers] = useState<UserWithRoles[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<UserWithRoles | null>(null);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [showRoleManagement, setShowRoleManagement] = useState(false);
  const [operationLoading, setOperationLoading] = useState(false);
  
  // Form states
  const [createUserForm, setCreateUserForm] = useState<CreateUserFormData>({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    employee_id: '',
    phone_number: '',
    department: '',
    position: '',
    role_id: undefined
  });
  
  const [editUserForm, setEditUserForm] = useState<EditUserFormData>({
    email: '',
    first_name: '',
    last_name: '',
    employee_id: '',
    phone_number: '',
    department: '',
    position: '',
    is_active: true
  });
  
  const [passwordResetForm, setPasswordResetForm] = useState<PasswordResetFormData>({
    new_password: '',
    new_password_confirm: '',
    reason: ''
  });

  // Load users and roles from API
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        try {
          // Try to load from API first
          const [usersData, rolesData] = await Promise.all([
            apiService.getUsers(),
            apiService.getRoles()
          ]);
          
          setUsers(usersData);
          setRoles(rolesData);
        } catch (apiError) {
          
          // Fallback to mock data
          setUsers(mockUsers);
          setRoles(mockRoles);
        }
      } catch (err: any) {
        console.error('Error loading data:', err);
        setError('Failed to load user data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Mock data (fallback)
  const mockUsers: UserWithRoles[] = [
    {
      id: 1,
      username: 'docadmin',
      email: 'admin@edms.local',
      first_name: 'Document',
      last_name: 'Admin',
      is_active: true,
      is_staff: true,
      is_superuser: true,
      date_joined: '2024-01-01T00:00:00Z',
      last_login: '2024-11-23T10:30:00Z',
      active_roles: [
        { id: 1, name: 'Document Admin', module: 'O1', permission_level: 'admin' }
      ]
    },
    {
      id: 2,
      username: 'author',
      email: 'author@edms.local',
      first_name: 'Jane',
      last_name: 'Author',
      is_active: true,
      is_staff: false,
      is_superuser: false,
      date_joined: '2024-01-02T00:00:00Z',
      last_login: '2024-11-23T09:15:00Z',
      active_roles: [
        { id: 2, name: 'Document Author', module: 'O1', permission_level: 'write' }
      ]
    }
  ];

  const mockRoles: Role[] = [
    { id: 1, name: 'Document Viewer', module: 'O1', permission_level: 'read', is_active: true },
    { id: 2, name: 'Document Author', module: 'O1', permission_level: 'write', is_active: true },
    { id: 3, name: 'Document Reviewer', module: 'O1', permission_level: 'review', is_active: true },
    { id: 4, name: 'Document Approver', module: 'O1', permission_level: 'approve', is_active: true },
    { id: 5, name: 'Document Admin', module: 'O1', permission_level: 'admin', is_active: true }
  ];

  // Handler functions
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setOperationLoading(true);
    
    try {
      await apiService.createUser(createUserForm);
      
      // Reload users
      const usersData = await apiService.getUsers();
      setUsers(usersData);
      
      // Reset form and close modal
      setCreateUserForm({
        username: '',
        email: '',
        password: '',
        password_confirm: '',
        first_name: '',
        last_name: '',
        employee_id: '',
        phone_number: '',
        department: '',
        position: '',
        role_id: undefined
      });
      setShowCreateUser(false);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setOperationLoading(false);
    }
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    
    setOperationLoading(true);
    
    try {
      await apiService.updateUser(selectedUser.id, editUserForm);
      
      // Reload users
      const usersData = await apiService.getUsers();
      setUsers(usersData);
      
      setShowEditUser(false);
      setSelectedUser(null);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to update user');
    } finally {
      setOperationLoading(false);
    }
  };

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    
    setOperationLoading(true);
    
    try {
      await apiService.resetPassword(
        selectedUser.id, 
        passwordResetForm.new_password,
        passwordResetForm.new_password_confirm,
        passwordResetForm.reason
      );
      
      setPasswordResetForm({
        new_password: '',
        new_password_confirm: '',
        reason: ''
      });
      setShowPasswordReset(false);
      setSelectedUser(null);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to reset password');
    } finally {
      setOperationLoading(false);
    }
  };

  const handleAssignRole = async (roleId: number, reason: string = '') => {
    if (!selectedUser) return;
    
    setOperationLoading(true);
    
    try {
      await apiService.assignRole(selectedUser.id, roleId, reason);
      
      // Reload users
      const usersData = await apiService.getUsers();
      setUsers(usersData);
      
      // Update selectedUser to reflect new roles
      const updatedUser = usersData.find(user => user.id === selectedUser.id);
      if (updatedUser) {
        setSelectedUser(updatedUser);
      }
      
      // Clear any existing errors on success
      setError(null);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || error.response?.data?.message || 'Failed to assign role');
    } finally {
      setOperationLoading(false);
    }
  };

  const handleRemoveRole = async (roleId: number, reason: string = '') => {
    if (!selectedUser) return;
    
    setOperationLoading(true);
    
    try {
      await apiService.removeRole(selectedUser.id, roleId, reason);
      
      // Reload users
      const usersData = await apiService.getUsers();
      setUsers(usersData);
      
      // Update selectedUser to reflect removed roles
      const updatedUser = usersData.find(user => user.id === selectedUser.id);
      if (updatedUser) {
        setSelectedUser(updatedUser);
      }
      
      // Clear any existing errors on success
      setError(null);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || error.response?.data?.message || 'Failed to remove role');
    } finally {
      setOperationLoading(false);
    }
  };

  const openEditUser = (user: UserWithRoles) => {
    setSelectedUser(user);
    setEditUserForm({
      email: user.email,
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      employee_id: user.employee_id || '',
      phone_number: user.phone_number || '',
      department: user.department || '',
      position: user.position || '',
      is_active: user.is_active
    });
    setShowEditUser(true);
  };

  const openPasswordReset = (user: UserWithRoles) => {
    setSelectedUser(user);
    setPasswordResetForm({
      new_password: '',
      new_password_confirm: '',
      reason: ''
    });
    setShowPasswordReset(true);
  };

  const openRoleManagement = (user: UserWithRoles) => {
    setSelectedUser(user);
    setShowRoleManagement(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className={`bg-white p-6 rounded-lg shadow ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white p-6 rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">User Management</h3>
            <p className="mt-1 text-sm text-gray-600">
              Manage users, roles, and permissions for the EDMS system
            </p>
          </div>
          <button
            onClick={() => setShowCreateUser(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Create User
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
          <button
            onClick={() => setError(null)}
            className="float-right text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      )}

      {/* Users List */}
      <div className="space-y-4">
        {users.map((user) => (
          <div key={user.id} className="border rounded-lg p-4 hover:bg-gray-50">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">
                      {user.first_name} {user.last_name}
                      {user.is_superuser && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Superuser
                        </span>
                      )}
                      {!user.is_active && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Inactive
                        </span>
                      )}
                    </h4>
                    <p className="text-sm text-gray-600">@{user.username} • {user.email}</p>
                    
                    {/* Active Roles */}
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(user.active_roles || []).map((role) => (
                        <span
                          key={role.id}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {role.name} ({role.permission_level})
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => openEditUser(user)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => openPasswordReset(user)}
                      className="text-sm text-yellow-600 hover:text-yellow-800"
                    >
                      Reset Password
                    </button>
                    <button
                      onClick={() => openRoleManagement(user)}
                      className="text-sm text-green-600 hover:text-green-800"
                    >
                      Manage Roles
                    </button>
                  </div>
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

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6 max-h-screen overflow-y-auto">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Create New User</h4>
            
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Username</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={createUserForm.username}
                  onChange={(e) => setCreateUserForm({...createUserForm, username: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={createUserForm.email}
                  onChange={(e) => setCreateUserForm({...createUserForm, email: e.target.value})}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">First Name</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={createUserForm.first_name}
                    onChange={(e) => setCreateUserForm({...createUserForm, first_name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Name</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={createUserForm.last_name}
                    onChange={(e) => setCreateUserForm({...createUserForm, last_name: e.target.value})}
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Password</label>
                <input
                  type="password"
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={createUserForm.password}
                  onChange={(e) => setCreateUserForm({...createUserForm, password: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Confirm Password</label>
                <input
                  type="password"
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={createUserForm.password_confirm}
                  onChange={(e) => setCreateUserForm({...createUserForm, password_confirm: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Initial Role (Optional)</label>
                <select
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={createUserForm.role_id || ''}
                  onChange={(e) => setCreateUserForm({...createUserForm, role_id: e.target.value ? Number(e.target.value) : undefined})}
                >
                  <option value="">Select a role...</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>{role.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateUser(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={operationLoading}
                  className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {operationLoading ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditUser && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Edit User: {selectedUser.username}</h4>
            
            <form onSubmit={handleEditUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={editUserForm.email}
                  onChange={(e) => setEditUserForm({...editUserForm, email: e.target.value})}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">First Name</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={editUserForm.first_name}
                    onChange={(e) => setEditUserForm({...editUserForm, first_name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Name</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={editUserForm.last_name}
                    onChange={(e) => setEditUserForm({...editUserForm, last_name: e.target.value})}
                  />
                </div>
              </div>
              
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    checked={editUserForm.is_active}
                    onChange={(e) => setEditUserForm({...editUserForm, is_active: e.target.checked})}
                  />
                  <span className="ml-2 text-sm text-gray-700">Active</span>
                </label>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowEditUser(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={operationLoading}
                  className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {operationLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Password Reset Modal */}
      {showPasswordReset && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Reset Password: {selectedUser.username}</h4>
            
            <form onSubmit={handlePasswordReset} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">New Password</label>
                <input
                  type="password"
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={passwordResetForm.new_password}
                  onChange={(e) => setPasswordResetForm({...passwordResetForm, new_password: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
                <input
                  type="password"
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={passwordResetForm.new_password_confirm}
                  onChange={(e) => setPasswordResetForm({...passwordResetForm, new_password_confirm: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Reason (Optional)</label>
                <textarea
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                  value={passwordResetForm.reason}
                  onChange={(e) => setPasswordResetForm({...passwordResetForm, reason: e.target.value})}
                  placeholder="Reason for password reset..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowPasswordReset(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={operationLoading}
                  className="px-4 py-2 bg-red-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                >
                  {operationLoading ? 'Resetting...' : 'Reset Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Role Management Modal */}
      {showRoleManagement && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full p-6 max-h-screen overflow-y-auto">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Manage Roles: {selectedUser.username}</h4>
            
            <div className="space-y-6">
              {/* Current Roles */}
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Current Roles</h5>
                <div className="space-y-2">
                  {(selectedUser.active_roles || []).map((role) => (
                    <div key={role.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{role.name} ({role.permission_level})</span>
                      <button
                        onClick={() => handleRemoveRole(role.id)}
                        disabled={operationLoading}
                        className="text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  {(!selectedUser.active_roles || selectedUser.active_roles.length === 0) && (
                    <p className="text-sm text-gray-500 italic">No roles assigned</p>
                  )}
                </div>
              </div>
              
              {/* Available Roles */}
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Available Roles</h5>
                <div className="space-y-2">
                  {roles.filter(role => 
                    !(selectedUser.active_roles || []).some(ar => ar.id === role.id)
                  ).map((role) => (
                    <div key={role.id} className="flex items-center justify-between p-3 border rounded">
                      <span className="text-sm">{role.name} ({role.permission_level})</span>
                      <button
                        onClick={() => handleAssignRole(role.id)}
                        disabled={operationLoading}
                        className="text-sm text-green-600 hover:text-green-800 disabled:opacity-50"
                      >
                        Assign
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex justify-end">
                <button
                  onClick={() => setShowRoleManagement(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;