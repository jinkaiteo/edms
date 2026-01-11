/**
 * UserSelector Component
 * 
 * Provides a searchable dropdown for selecting reviewers and approvers
 * with workload indicators and availability status.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ChevronDownIcon, UserIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  workload_status: 'low' | 'normal' | 'high';
  is_available: boolean;
  active_reviews?: number;
  active_approvals?: number;
  department?: string;
  approval_level?: string;
}

interface UserSelectorProps {
  type: 'reviewer' | 'approver';
  selectedUserId?: number;
  onSelect: (user: User | null) => void;
  documentType?: string;
  criticality?: string;
  disabled?: boolean;
  placeholder?: string;
}

const UserSelector: React.FC<UserSelectorProps> = ({
  type,
  selectedUserId,
  onSelect,
  documentType,
  criticality,
  disabled = false,
  placeholder
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Fetch users based on type
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (documentType) params.append('document_type', documentType);
      if (criticality) params.append('criticality', criticality);

      const endpoint = type === 'reviewer' ? 'reviewers' : 'approvers';
      const response = await fetch(`/api/v1/workflows/users/${endpoint}/?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const userList = type === 'reviewer' ? data.reviewers : data.approvers;
        setUsers(userList);

        // Set selected user if selectedUserId is provided
        if (selectedUserId) {
          const selected = userList.find((user: User) => user.id === selectedUserId);
          setSelectedUser(selected || null);
        }
      } else {
        console.error('Failed to fetch users');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  }, [type, documentType, criticality, selectedUserId]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Filter users based on search term
  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelectUser = (user: User) => {
    setSelectedUser(user);
    onSelect(user);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleClearSelection = () => {
    setSelectedUser(null);
    onSelect(null);
    setSearchTerm('');
  };

  const getWorkloadColor = (status: string) => {
    switch (status) {
      case 'low': return 'text-green-600';
      case 'normal': return 'text-yellow-600';
      case 'high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getWorkloadIcon = (user: User) => {
    if (!user.is_available) {
      return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
    }
    return null;
  };

  return (
    <div className="relative">
      {/* Selected User Display / Dropdown Trigger */}
      <div
        className={`
          relative w-full cursor-pointer rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-left shadow-sm
          focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'hover:border-gray-400'}
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        {selectedUser ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <UserIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">
                    {user.first_name && user.last_name
                      ? `${user.first_name} ${user.last_name}`
                      : user.username
                    }
                  </span>
                  {getWorkloadIcon(user)}
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <span>{user.email}</span>
                  <span className="text-gray-300">•</span>
                  <span className={getWorkloadColor(user.workload_status)}>
                    {user.workload_status} workload
                  </span>
                  {type === 'reviewer' && user.active_reviews !== undefined && (
                    <>
                      <span className="text-gray-300">•</span>
                      <span>{user.active_reviews} active reviews</span>
                    </>
                  )}
                  {type === 'approver' && user.active_approvals !== undefined && (
                    <>
                      <span className="text-gray-300">•</span>
                      <span>{user.active_approvals} active approvals</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <button
              type="button"
              className="text-gray-400 hover:text-gray-600"
              onClick={(e) => {
                e.stopPropagation();
                handleClearSelection();
              }}
            >
              ×
            </button>
          </div>
        ) : (
          <span className="text-gray-500">
            {placeholder || `Select ${type}...`}
          </span>
        )}
        
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <ChevronDownIcon className="h-5 w-5 text-gray-400" />
        </div>
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder={`Search ${type}s...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>

          {/* Loading State */}
          {loading && (
            <div className="px-3 py-2 text-sm text-gray-500">
              Loading {type}s...
            </div>
          )}

          {/* User List */}
          {!loading && filteredUsers.length === 0 && (
            <div className="px-3 py-2 text-sm text-gray-500">
              {searchTerm ? `No ${type}s found matching "${searchTerm}"` : `No ${type}s available`}
            </div>
          )}

          {!loading && filteredUsers.map((user) => (
            <div
              key={user.id}
              className={`
                relative cursor-pointer select-none py-2 px-3 hover:bg-indigo-50
                ${selectedUser?.id === user.id ? 'bg-indigo-100' : ''}
                ${!user.is_available ? 'opacity-60' : ''}
              `}
              onClick={() => handleSelectUser(user)}
            >
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <UserIcon className={`h-5 w-5 ${user.is_available ? 'text-gray-400' : 'text-red-400'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">
                      {user.first_name && user.last_name
                        ? `${user.first_name} ${user.last_name}`
                        : user.username
                      }
                    </span>
                    {!user.is_available && (
                      <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
                    )}
                    {type === 'approver' && user.approval_level === 'senior' && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        Senior
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <span>{user.email}</span>
                    <span className="text-gray-300">•</span>
                    <span className={getWorkloadColor(user.workload_status)}>
                      {user.workload_status} workload
                    </span>
                    {type === 'reviewer' && user.active_reviews !== undefined && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span>{user.active_reviews} reviews</span>
                      </>
                    )}
                    {type === 'approver' && user.active_approvals !== undefined && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span>{user.active_approvals} approvals</span>
                      </>
                    )}
                    {user.department && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span>{user.department}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserSelector;