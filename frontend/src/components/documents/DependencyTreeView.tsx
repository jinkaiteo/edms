import React, { useState } from 'react';

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

interface DependencyTreeViewProps {
  chain: DependencyChain;
}

const DependencyTreeView: React.FC<DependencyTreeViewProps> = ({ chain }) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['dependencies', 'dependents'])
  );

  // Check if any nodes are at max depth (indicating there might be more beyond)
  const MAX_DEPTH = 5;
  const hasNodesAtMaxDepth = (nodes: DependencyNode[]) => {
    return nodes.some(node => node.depth >= MAX_DEPTH);
  };

  const getNodesAtMaxDepth = (nodes: DependencyNode[]) => {
    return nodes.filter(node => node.depth >= MAX_DEPTH);
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const renderDependencyNode = (node: DependencyNode, direction: 'in' | 'out', index: number) => {
    const indent = Math.min(node.depth - 1, 5) * 20; // Max 5 levels of indentation
    const isAtMaxDepth = node.depth >= MAX_DEPTH;

    return (
      <div key={`${direction}-${node.document_number}-${node.depth}-${index}`}>
        <div
          className={`flex items-center py-2 px-3 border rounded mb-2 ${
            isAtMaxDepth 
              ? 'border-orange-300 bg-orange-50' 
              : 'border-gray-200 bg-white'
          }`}
          style={{ marginLeft: `${indent}px` }}
        >
          <div className="flex items-center space-x-2 flex-1">
            <div className={`w-2 h-2 rounded-full ${
              isAtMaxDepth ? 'bg-orange-400' : 'bg-blue-400'
            }`}></div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {node.document_number}
                </p>

                <span
                  className={`text-xs px-2 py-1 rounded-full ${
                    node.is_critical
                      ? 'bg-red-100 text-red-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  {node.type}
                </span>

                {node.is_critical && (
                  <span className="text-xs bg-red-200 text-red-900 px-2 py-1 rounded-full font-medium">
                    Critical
                  </span>
                )}
                
                {isAtMaxDepth && (
                  <span className="text-xs bg-orange-200 text-orange-900 px-2 py-1 rounded-full font-medium">
                    ⚠️ Max Depth
                  </span>
                )}
              </div>

              <p className="text-xs text-gray-600 truncate mt-1">{node.title}</p>
            </div>

            <div className="text-xs text-gray-400">L{node.depth}</div>
          </div>
        </div>
        
        {isAtMaxDepth && (
          <div 
            className="text-xs text-orange-700 bg-orange-50 border-l-2 border-orange-400 px-3 py-1.5 mb-2 ml-2"
            style={{ marginLeft: `${indent + 10}px` }}
          >
            💡 This document may have deeper dependencies not shown (limit: {MAX_DEPTH} levels)
          </div>
        )}
      </div>
    );
  };

  const totalDependencies = chain.dependencies.length;
  const totalDependents = chain.dependents.length;
  const hasDependencies = totalDependencies > 0 || totalDependents > 0;

  if (!hasDependencies) {
    return (
      <div className="p-4 text-center border border-gray-200 rounded-lg bg-gray-50">
        <div className="text-gray-400 mb-2">
          <svg
            className="w-8 h-8 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
        </div>
        <p className="text-sm text-gray-600">No dependencies found</p>
        <p className="text-xs text-gray-500 mt-1">
          This document has no dependency relationships
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Dependencies (what this document depends on) */}
      {totalDependencies > 0 && (
        <div>
          <button
            onClick={() => toggleSection('dependencies')}
            className="flex items-center justify-between w-full text-left"
          >
            <h4 className="text-sm font-medium text-gray-700">
              📥 Dependencies ({totalDependencies})
            </h4>
            <svg
              className={`w-4 h-4 transition-transform ${
                expandedSections.has('dependencies') ? 'rotate-90' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>

          <p className="text-xs text-gray-600 mt-1 mb-3">
            Documents that this document depends on
          </p>

          {expandedSections.has('dependencies') && (
            <div className="space-y-1">
              {chain.dependencies.map((node, index) =>
                renderDependencyNode(node, 'in', index)
              )}
            </div>
          )}
        </div>
      )}

      {/* Dependents (what depends on this document) */}
      {totalDependents > 0 && (
        <div>
          <button
            onClick={() => toggleSection('dependents')}
            className="flex items-center justify-between w-full text-left"
          >
            <h4 className="text-sm font-medium text-gray-700">
              📤 Dependents ({totalDependents})
            </h4>
            <svg
              className={`w-4 h-4 transition-transform ${
                expandedSections.has('dependents') ? 'rotate-90' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>

          <p className="text-xs text-gray-600 mt-1 mb-3">
            Documents that depend on this document
          </p>

          {expandedSections.has('dependents') && (
            <div className="space-y-1">
              {chain.dependents.map((node, index) =>
                renderDependencyNode(node, 'out', index)
              )}
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="pt-3 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <h5 className="font-medium text-gray-700 mb-1">Dependency Types:</h5>
            <div className="space-y-1 text-gray-600">
              <div>• References: Cites content</div>
              <div>• Implements: Implements requirements</div>
              <div>• Template: Based on template</div>
            </div>
          </div>
          <div>
            <h5 className="font-medium text-gray-700 mb-1">Indicators:</h5>
            <div className="space-y-1 text-gray-600">
              <div>• L1, L2: Dependency depth level</div>
              <div>• Critical: Requires notification</div>
              <div>• ⚠️ Complex chains need review</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DependencyTreeView;
