import React from 'react';

const Notifications: React.FC = () => {
  const handleViewTasks = () => {
    window.location.href = '/my-tasks';
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-800">
            Notifications
          </h1>
          <p className="text-sm text-gray-600 mt-2">
            ✅ Simplified notification system operational
          </p>
        </div>

        <div className="p-6">
          <div className="text-center py-8">
            <div className="text-blue-600 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">
              Simplified Notification System Active
            </h3>
            <p className="text-gray-600 mb-6">
              Your workflow tasks and notifications are available through the Active Documents page.
              This simplified system provides reliable task visibility.
            </p>
            <button
              onClick={handleViewTasks}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              View Active Documents
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Notifications;
