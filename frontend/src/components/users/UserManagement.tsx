import React, { useState, useEffect } from 'react';
import PasswordInput from '../common/PasswordInput.tsx';
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
  roles: number[]; // Array of role IDs to assign
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
    roles: []
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
        
        // Load from API only - no mock data fallback
        const [usersData, rolesData] = await Promise.all([
          apiService.getUsers(),
          apiService.getRoles()
        ]);
        
        setUsers(usersData || []);
        setRoles(rolesData || []);
      } catch (err: any) {
        console.error('Error loading data:', err);
        setError('Failed to load user data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);


  // Handler functions
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setOperationLoading(true);
    
    try {
      // Create the user first
      const newUser = await apiService.createUser(createUserForm);
      
      // Assign selected roles if any
      if (createUserForm.roles.length > 0) {
        for (const roleId of createUserForm.roles) {
          try {
            await apiService.assignRole(newUser.id, roleId, 'Initial role assignment during user creation');
          } catch (roleError: any) {
            console.warn(`Failed to assign role ${roleId} to user ${newUser.username}:`, roleError);
            // Continue with other roles even if one fails
          }
        }
      }
      
      // Reload users to get updated role information
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
        roles: []
      });
      setShowCreateUser(false);
      
      // Clear any errors on success
      setError(null);
      
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

  const handleGrantSuperuser = async () => {
    if (!selectedUser) return;
    
    const reason = prompt('Please provide a reason for granting superuser status:');
    if (!reason) return; // User cancelled
    
    setOperationLoading(true);
    try {
      const response = await apiService.post(`/users/users/${selectedUser.id}/grant_superuser/`, {
        reason
      });
      
      // Update the selected user with new superuser status
      const updatedUser = await apiService.get(`/users/users/${selectedUser.id}/`);
      setSelectedUser(updatedUser.data);
      
      // Update user in the list
      setUsers(users.map(u => 
        u.id === selectedUser.id ? { ...u, is_superuser: true, is_staff: true } : u
      ));
      
      alert(`✅ Superuser status granted to ${selectedUser.username}`);
      setError(null);
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Failed to grant superuser status';
      setError(errorMessage);
      alert(`❌ ${errorMessage}`);
    } finally {
      setOperationLoading(false);
    }
  };

  const handleRevokeSuperuser = async () => {
    if (!selectedUser) return;
    
    const confirmed = window.confirm(
      `⚠️ Are you sure you want to revoke superuser status from ${selectedUser.username}?\n\n` +
      `This will remove all admin privileges. If this is the last superuser, the operation will be blocked.`
    );
    if (!confirmed) return;
    
    const reason = prompt('Please provide a reason for revoking superuser status:');
    if (!reason) return; // User cancelled
    
    setOperationLoading(true);
    try {
      const response = await apiService.post(`/users/users/${selectedUser.id}/revoke_superuser/`, {
        reason
      });
      
      // Update the selected user with new superuser status
      const updatedUser = await apiService.get(`/users/users/${selectedUser.id}/`);
      setSelectedUser(updatedUser.data);
      
      // Update user in the list
      setUsers(users.map(u => 
        u.id === selectedUser.id ? { ...u, is_superuser: false } : u
      ));
      
      alert(`✅ Superuser status revoked from ${selectedUser.username}`);
      setError(null);
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Failed to revoke superuser status';
      const errorDetail = error.response?.data?.detail;
      
      if (errorDetail) {
        alert(`❌ ${errorMessage}\n\n${errorDetail}`);
      } else {
        alert(`❌ ${errorMessage}`);
      }
      setError(errorMessage);
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
                <PasswordInput
                  required
                  minLength={12}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={createUserForm.password}
                  onChange={(e) => setCreateUserForm({...createUserForm, password: e.target.value})}
                  placeholder="Enter secure password..."
                />
                <div className="mt-1 flex items-center text-xs text-gray-500">
                  <svg className="w-4 h-4 mr-1 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  Password must be at least 12 characters long
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Confirm Password</label>
                <PasswordInput
                  required
                  minLength={12}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={createUserForm.password_confirm}
                  onChange={(e) => setCreateUserForm({...createUserForm, password_confirm: e.target.value})}
                  placeholder="Confirm password..."
                />
                {createUserForm.password && createUserForm.password_confirm && createUserForm.password !== createUserForm.password_confirm && (
                  <div className="mt-1 flex items-center text-xs text-red-600">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Passwords do not match
                  </div>
                )}
              </div>
              
              {/* Department and Position */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Department</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={createUserForm.department}
                    onChange={(e) => setCreateUserForm({...createUserForm, department: e.target.value})}
                    placeholder="e.g., Quality Assurance"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Position</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={createUserForm.position}
                    onChange={(e) => setCreateUserForm({...createUserForm, position: e.target.value})}
                    placeholder="e.g., QA Manager"
                  />
                </div>
              </div>
              
              {/* Role Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Assign Roles</label>
                <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-200 rounded p-3">
                  {roles.map((role) => (
                    <label key={role.id} className="flex items-center">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                        checked={createUserForm.roles.includes(role.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setCreateUserForm({
                              ...createUserForm,
                              roles: [...createUserForm.roles, role.id]
                            });
                          } else {
                            setCreateUserForm({
                              ...createUserForm,
                              roles: createUserForm.roles.filter(id => id !== role.id)
                            });
                          }
                        }}
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        {role.name} ({role.permission_level})
                      </span>
                    </label>
                  ))}
                  {roles.length === 0 && (
                    <p className="text-sm text-gray-500 italic">Loading roles...</p>
                  )}
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  Select one or more roles for the user. Roles can be modified later through "Manage Roles".
                </div>
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
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full my-8 max-h-[90vh] overflow-y-auto p-6">
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
              
              {/* Department and Position */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Department</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={editUserForm.department}
                    onChange={(e) => setEditUserForm({...editUserForm, department: e.target.value})}
                    placeholder="e.g., Quality Assurance"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Position</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    value={editUserForm.position}
                    onChange={(e) => setEditUserForm({...editUserForm, position: e.target.value})}
                    placeholder="e.g., QA Manager"
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
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full my-8 max-h-[90vh] overflow-y-auto p-6">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Reset Password: {selectedUser.username}</h4>
            
            <form onSubmit={handlePasswordReset} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">New Password</label>
                <PasswordInput
                  required
                  minLength={12}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={passwordResetForm.new_password}
                  onChange={(e) => setPasswordResetForm({...passwordResetForm, new_password: e.target.value})}
                  placeholder="Enter new secure password..."
                />
                <div className="mt-1 flex items-center text-xs text-gray-500">
                  <svg className="w-4 h-4 mr-1 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  Password must be at least 12 characters long
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
                <PasswordInput
                  required
                  minLength={12}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  value={passwordResetForm.new_password_confirm}
                  onChange={(e) => setPasswordResetForm({...passwordResetForm, new_password_confirm: e.target.value})}
                  placeholder="Confirm new password..."
                />
                {passwordResetForm.new_password && passwordResetForm.new_password_confirm && passwordResetForm.new_password !== passwordResetForm.new_password_confirm && (
                  <div className="mt-1 flex items-center text-xs text-red-600">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Passwords do not match
                  </div>
                )}
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
              {/* Superuser Status */}
              <div className="border-b border-gray-200 pb-4">
                <h5 className="text-sm font-medium text-gray-700 mb-3">Superuser Status</h5>
                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${selectedUser.is_superuser ? 'bg-purple-500' : 'bg-gray-300'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {selectedUser.is_superuser ? '⭐ Superuser' : 'Regular User'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {selectedUser.is_superuser 
                          ? 'Full admin access to all system functions' 
                          : 'Standard user permissions based on assigned roles'}
                      </p>
                    </div>
                  </div>
                  {selectedUser.is_superuser ? (
                    <button
                      onClick={() => handleRevokeSuperuser()}
                      disabled={operationLoading}
                      className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {operationLoading ? 'Processing...' : 'Revoke Superuser'}
                    </button>
                  ) : (
                    <button
                      onClick={() => handleGrantSuperuser()}
                      disabled={operationLoading}
                      className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {operationLoading ? 'Processing...' : 'Grant Superuser'}
                    </button>
                  )}
                </div>
              </div>

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