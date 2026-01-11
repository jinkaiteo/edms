import React from 'react';

interface CircularDependencyError {
  non_field_errors?: string[];
  dependency_chain_preview?: Array<{
    document_id: number;
    type: string;
    is_critical: boolean;
  }>;
}

interface CircularDependencyAlertProps {
  error: CircularDependencyError | null;
  onDismiss: () => void;
}

const CircularDependencyAlert: React.FC<CircularDependencyAlertProps> = ({
  error,
  onDismiss
}) => {
  if (!error?.non_field_errors?.some(err => err.includes('Circular dependency detected'))) {
    return null;
  }

  const circularError = error.non_field_errors.find(err => 
    err.includes('Circular dependency detected')
  );

  return (
    <div className="px-6 py-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800 mb-2">
            🔄 Circular Dependency Detected
          </h3>
          
          <div className="text-sm text-red-700 mb-3">
            <p className="mb-2">{circularError}</p>
            <p className="text-xs">
              This would create a dependency loop where documents depend on each other in a circle, 
              which can cause system issues and infinite loops.
            </p>
          </div>

          {error.dependency_chain_preview && error.dependency_chain_preview.length > 0 && (
            <div className="mb-3">
              <h4 className="text-xs font-medium text-red-800 mb-1">Existing Dependency Chain:</h4>
              <div className="text-xs text-red-600 bg-red-100 p-2 rounded">
                {error.dependency_chain_preview.map((dep, index) => (
                  <div key={dep.document_id} className="flex items-center">
                    <span>Document {dep.document_id}</span>
                    <span className="mx-1 text-red-400">({dep.type})</span>
                    {dep.is_critical && (
                      <span className="ml-1 text-xs bg-red-200 text-red-800 px-1 rounded">
                        Critical
                      </span>
                    )}
                    {index < error.dependency_chain_preview!.length - 1 && (
                      <span className="mx-2">→</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-red-100 p-3 rounded text-xs text-red-800 mb-3">
            <h4 className="font-medium mb-1">💡 How to Fix:</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Remove one of the dependencies to break the cycle</li>
              <li>Consider if the dependency relationship is really necessary</li>
              <li>Use a different dependency type (e.g., "References" instead of "Implements")</li>
              <li>Create a parent document that both documents can depend on instead</li>
            </ul>
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={onDismiss}
              className="text-xs text-red-600 hover:text-red-800 font-medium"
            >
              Dismiss
            </button>
            
            <div className="text-xs text-red-600">
              Contact system administrator if you need help resolving this issue
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CircularDependencyAlert;