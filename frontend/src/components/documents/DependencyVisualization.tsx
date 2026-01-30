import React, { useState, useEffect } from 'react';
import apiService from '../../services/api.ts';
import DependencyTreeView from './DependencyTreeView.tsx';
import DependencyGraphView from './DependencyGraphView.tsx';

interface DependencyNode {
  id: number;
  document_number: string;
  title: string;
  type: string;
  is_critical: boolean;
  depth: number;
}

interface DependencyChain {
  dependencies: DependencyNode[];
  dependents: DependencyNode[];
}

interface DependencyVisualizationProps {
  documentUuid: string;
  documentNumber: string;
  onCircularDependencyDetected?: (hasCircular: boolean) => void;
}

const DependencyVisualization: React.FC<DependencyVisualizationProps> = ({
  documentUuid,
  documentNumber,
  onCircularDependencyDetected
}) => {
  const [chain, setChain] = useState<DependencyChain | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'tree' | 'graph'>('tree');

  useEffect(() => {
    if (documentUuid) {
      loadDependencyChain();
    }
  }, [documentUuid]);

  const loadDependencyChain = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiService.get(`/documents/documents/${documentUuid}/dependency_chain/?max_depth=5`);
      
      console.log('🔍 API Response:', response);
      console.log('🔍 Response.data:', response.data);
      
      // Check if data is directly in response or nested
      const chainData = response.dependency_chain || response.data?.dependency_chain || response.data;
      
      console.log('📊 Chain Data:', chainData);
      
      // Extract current document info from the response
      const currentDoc = response.document || response.data?.document;
      console.log('📄 Current Document:', currentDoc);
      
      if (chainData && (chainData.dependencies || chainData.dependents)) {
        setChain({
          dependencies: chainData.dependencies || [],
          dependents: chainData.dependents || [],
          currentDocumentId: currentDoc?.id, // Add current document ID
          currentDocumentNumber: currentDoc?.document_number
        });
        
        // Check for potential circular dependencies
        const totalDeps = (chainData.dependencies?.length || 0) + (chainData.dependents?.length || 0);
        const hasComplexChain = totalDeps > 5;
        
        if (onCircularDependencyDetected) {
          onCircularDependencyDetected(hasComplexChain);
        }
      } else {
        console.warn('⚠️ No valid dependency chain data found');
        setChain({ dependencies: [], dependents: [] });
      }
      
    } catch (error: any) {
      console.error('❌ Failed to load dependency chain:', error);
      setError('Failed to load dependency visualization');
      setChain({ dependencies: [], dependents: [] });
    } finally {
      setLoading(false);
    }
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center p-4 border border-gray-200 rounded-lg bg-gray-50">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm text-gray-600">Loading dependency visualization...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (!chain) {
    return null;
  }

  const totalDependencies = chain.dependencies.length;
  const totalDependents = chain.dependents.length;

  return (
    <div className="border border-gray-200 rounded-lg bg-gray-50">
      <div className="px-4 py-3 border-b border-gray-200 bg-white rounded-t-lg">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">
            🔗 Dependency Visualization
          </h3>
          
          <div className="flex items-center space-x-4">
            <div className="text-xs text-gray-500">
              {totalDependencies + totalDependents} connections
            </div>
            
            {/* View Mode Toggle */}
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('tree')}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                  viewMode === 'tree'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🌳 Tree View
              </button>
              <button
                onClick={() => setViewMode('graph')}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                  viewMode === 'graph'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🕸️ Graph View
              </button>
            </div>
          </div>
        </div>
        
        {(totalDependencies + totalDependents > 10) && (
          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
            ⚠️ Complex dependency chain detected ({totalDependencies + totalDependents} connections). Review for potential circular dependencies.
          </div>
        )}
      </div>

      <div className="p-4">
        {viewMode === 'tree' ? (
          <DependencyTreeView chain={chain} />
        ) : (
          <DependencyGraphView chain={chain} currentDocumentNumber={documentNumber} />
        )}
      </div>
    </div>
  );
};

export default DependencyVisualization;