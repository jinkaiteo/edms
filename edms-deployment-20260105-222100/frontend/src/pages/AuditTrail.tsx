import React from 'react';
import Layout from '../components/common/Layout.tsx';
import AuditTrailViewer from '../components/audit/AuditTrailViewer.tsx';

const AuditTrail: React.FC = () => {
  return (
    <Layout>
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <div className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="py-6">
              <h1 className="text-3xl font-bold text-gray-900">Audit Trail</h1>
              <p className="mt-1 text-sm text-gray-500">
                View all system activities and compliance events
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <AuditTrailViewer />
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AuditTrail;