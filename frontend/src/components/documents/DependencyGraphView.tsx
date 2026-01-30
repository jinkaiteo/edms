import React, { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
  NodeProps,
  Handle,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Custom Node Component
const CustomNode = ({ data }: NodeProps) => {
  return (
    <div className="px-3 py-2 text-center">
      <Handle type="target" position={Position.Left} />
      <div className="font-semibold text-sm">{data.documentNumber || data.label}</div>
      {data.title && (
        <div className="text-xs text-gray-600 mt-1 truncate max-w-[160px]">
          {data.title}
        </div>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

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
  currentDocumentId?: number;
  currentDocumentNumber?: string;
}

interface DependencyGraphViewProps {
  chain: DependencyChain;
  currentDocumentNumber: string;
}

const DependencyGraphView: React.FC<DependencyGraphViewProps> = ({ chain, currentDocumentNumber }) => {
  // Define node types
  const nodeTypes = useMemo(() => ({
    custom: CustomNode,
  }), []);

  // Check for nodes at max depth
  const MAX_DEPTH = 5;
  const nodesAtMaxDepth = useMemo(() => {
    const allNodes = [...chain.dependencies, ...chain.dependents];
    return allNodes.filter(node => node.depth >= MAX_DEPTH);
  }, [chain]);

  const hasNodesAtMaxDepth = nodesAtMaxDepth.length > 0;

  // Convert dependency data to React Flow nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    console.log('🔍 DependencyGraphView: Building graph for', currentDocumentNumber);
    console.log('  Dependencies:', chain.dependencies);
    console.log('  Dependents:', chain.dependents);
    
    const nodeMap = new Map<string, Node>();
    const edgeList: Edge[] = [];
    
    // Build ID to document number map first (from backend data)
    const idToDocNumber = new Map<number, string>();
    
    // Add current document ID to the map (critical for parent_id lookups!)
    if (chain.currentDocumentId) {
      idToDocNumber.set(chain.currentDocumentId, currentDocumentNumber);
      console.log(`  Map: ID ${chain.currentDocumentId} → ${currentDocumentNumber} (CURRENT)`);
    }
    
    // Add all nodes to the map
    chain.dependencies.forEach(dep => {
      if (dep.id) {
        idToDocNumber.set(dep.id, dep.document_number);
        console.log(`  Map: ID ${dep.id} → ${dep.document_number}`);
      }
    });
    chain.dependents.forEach(dep => {
      if (dep.id) {
        idToDocNumber.set(dep.id, dep.document_number);
        console.log(`  Map: ID ${dep.id} → ${dep.document_number}`);
      }
    });
    
    console.log('  ID to DocNumber Map:', idToDocNumber);
    
    // Helper to create or get a node
    const getOrCreateNode = (dep: DependencyNode, isCurrent: boolean = false): Node => {
      const nodeId = dep.document_number;
      
      if (nodeMap.has(nodeId)) {
        return nodeMap.get(nodeId)!;
      }
      
      const isAtMaxDepth = dep.depth >= MAX_DEPTH;
      
      const node: Node = {
        id: nodeId,
        type: 'custom',
        data: { 
          label: dep.document_number,
          documentNumber: dep.document_number,
          documentId: dep.id, // Store ID for parent matching
          title: dep.title,
          isCritical: dep.is_critical,
          isCurrent: isCurrent,
          isAtMaxDepth: isAtMaxDepth,
        },
        position: { x: 0, y: 0 }, // Will be auto-laid out
        style: {
          background: isCurrent ? '#3B82F6' : isAtMaxDepth ? '#FEF3C7' : dep.is_critical ? '#FEE2E2' : '#F3F4F6',
          color: isCurrent ? '#ffffff' : '#1F2937',
          border: `3px solid ${isCurrent ? '#2563EB' : isAtMaxDepth ? '#F59E0B' : dep.is_critical ? '#EF4444' : '#D1D5DB'}`,
          borderRadius: '8px',
          width: 180,
          fontSize: '12px',
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };
      
      nodeMap.set(nodeId, node);
      return node;
    };
    
    // Create current document node (center)
    const currentNode: Node = {
      id: currentDocumentNumber,
      type: 'custom',
      data: { 
        label: currentDocumentNumber,
        documentNumber: currentDocumentNumber,
        title: 'Current Document',
        isCurrent: true,
      },
      position: { x: 400, y: 300 }, // Center position
      style: {
        background: '#3B82F6',
        color: '#ffffff',
        border: '3px solid #2563EB',
        borderRadius: '12px',
        width: 200,
        fontSize: '13px',
        fontWeight: 'bold',
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    };
    nodeMap.set(currentDocumentNumber, currentNode);
    
    // Track unique edges to avoid duplicates
    const edgeKeys = new Set();
    
    // Group nodes by depth for proper positioning
    const depsByDepth = new Map<number, DependencyNode[]>();
    chain.dependencies.forEach(dep => {
      if (!depsByDepth.has(dep.depth)) {
        depsByDepth.set(dep.depth, []);
      }
      depsByDepth.get(dep.depth)!.push(dep);
    });
    
    // Process dependencies (nodes that current document depends on) - place to the left
    chain.dependencies.forEach((dep, index) => {
      console.log(`\n🔍 Processing DEPENDENCY ${index}:`, dep);
      console.log(`  Has parent_id? ${dep.parent_id ? 'YES' : 'NO'}`);
      console.log(`  parent_id value:`, dep.parent_id);
      console.log(`  In map? ${dep.parent_id ? idToDocNumber.has(dep.parent_id) : 'N/A'}`);
      
      const node = getOrCreateNode(dep, false);
      // Position based on depth (left side, further left = deeper)
      const xPos = 400 - (dep.depth * 200); // Further left for each depth level
      const nodesAtThisDepth = depsByDepth.get(dep.depth)!;
      const indexAtDepth = nodesAtThisDepth.indexOf(dep);
      const yPos = 150 + (indexAtDepth * 120);
      node.position = { x: xPos, y: yPos };
      
      // Create edge using parent_id information
      // For DEPENDENCIES: arrows point FROM dependency TO what depends on it
      // This shows "current doc depends on this"
      let sourceNumber: string;
      let targetNumber: string;
      
      if (dep.parent_id && idToDocNumber.has(dep.parent_id)) {
        // Parent exists in our map - create edge FROM this node TO parent
        // REVERSED for dependencies: dep → parent (showing "parent depends on dep")
        sourceNumber = dep.document_number;
        targetNumber = idToDocNumber.get(dep.parent_id)!;
        console.log(`  ✅ Dependency edge: ${sourceNumber} → ${targetNumber} (parent_id: ${dep.parent_id})`);
      } else {
        // Direct dependency - edge goes FROM this node TO current document
        sourceNumber = dep.document_number;
        targetNumber = currentDocumentNumber;
        console.log(`  ✅ Dependency edge (direct): ${sourceNumber} → ${targetNumber} (no parent_id)`);
      }
      
      const edgeId = `${sourceNumber}-${targetNumber}`;
      
      // Only add if not already added (prevents duplicate edges)
      if (!edgeKeys.has(edgeId)) {
        edgeKeys.add(edgeId);
        edgeList.push({
          id: edgeId,
          source: sourceNumber,
          target: targetNumber,
          type: 'smoothstep',
          label: dep.type,
          labelStyle: { fill: '#6B7280', fontSize: 10 },
          labelBgPadding: [8, 4],
          labelBgBorderRadius: 4,
          labelBgStyle: { fill: '#F9FAFB', fillOpacity: 0.9 },
          style: { 
            stroke: dep.is_critical ? '#EF4444' : '#9CA3AF',
            strokeWidth: dep.is_critical ? 3 : 2,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: dep.is_critical ? '#EF4444' : '#9CA3AF',
          },
          animated: dep.is_critical,
        });
      }
    });
    
    // Group dependents by depth
    const depentsByDepth = new Map<number, DependencyNode[]>();
    chain.dependents.forEach(dep => {
      if (!depentsByDepth.has(dep.depth)) {
        depentsByDepth.set(dep.depth, []);
      }
      depentsByDepth.get(dep.depth)!.push(dep);
    });
    
    // Process dependents (nodes that depend on current document) - place to the right
    chain.dependents.forEach((dep, index) => {
      console.log(`\n🔍 Processing dependent ${index}:`, dep);
      console.log(`  Has parent_id? ${dep.parent_id ? 'YES' : 'NO'}`);
      console.log(`  parent_id value:`, dep.parent_id);
      console.log(`  In map? ${dep.parent_id ? idToDocNumber.has(dep.parent_id) : 'N/A'}`);
      
      const node = getOrCreateNode(dep, false);
      // Position based on depth (right side, further right = deeper)
      const xPos = 600 + (dep.depth * 200); // Further right for each depth level
      const nodesAtThisDepth = depentsByDepth.get(dep.depth)!;
      const indexAtDepth = nodesAtThisDepth.indexOf(dep);
      const yPos = 150 + (indexAtDepth * 120);
      node.position = { x: xPos, y: yPos };
      
      // Create edge using parent_id information
      let sourceNumber: string;
      let targetNumber: string;
      
      if (dep.parent_id && idToDocNumber.has(dep.parent_id)) {
        // Parent exists in our map - create edge from parent to this node
        sourceNumber = idToDocNumber.get(dep.parent_id)!;
        targetNumber = dep.document_number;
        console.log(`  ✅ Dependent edge: ${sourceNumber} → ${targetNumber} (parent_id: ${dep.parent_id})`);
      } else {
        // Direct dependent - edge goes FROM current document TO this node
        sourceNumber = currentDocumentNumber;
        targetNumber = dep.document_number;
        console.log(`  ✅ Dependent edge (direct): ${sourceNumber} → ${targetNumber} (no parent_id)`);
      }
      
      const edgeId = `${sourceNumber}-${targetNumber}`;
      
      // Only add if not already added (prevents duplicate edges)
      if (!edgeKeys.has(edgeId)) {
        edgeKeys.add(edgeId);
        console.log(`    Adding edge: ${edgeId}`);
        edgeList.push({
          id: edgeId,
          source: sourceNumber,
          target: targetNumber,
          type: 'smoothstep',
          label: dep.type,
          labelStyle: { fill: '#6B7280', fontSize: 10 },
          labelBgPadding: [8, 4],
          labelBgBorderRadius: 4,
          labelBgStyle: { fill: '#F9FAFB', fillOpacity: 0.9 },
          style: { 
            stroke: dep.is_critical ? '#EF4444' : '#9CA3AF',
            strokeWidth: dep.is_critical ? 3 : 2,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: dep.is_critical ? '#EF4444' : '#9CA3AF',
          },
          animated: dep.is_critical,
        });
      }
    });
    
    return {
      nodes: Array.from(nodeMap.values()),
      edges: edgeList,
    };
  }, [chain, currentDocumentNumber]);
  
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    console.log('Node clicked:', node.data.documentNumber);
    // Could add navigation here
  }, []);
  
  return (
    <div className="space-y-2">
      {hasNodesAtMaxDepth && (
        <div className="bg-orange-50 border border-orange-300 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <div className="text-orange-500 mt-0.5">⚠️</div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-orange-900">Maximum Depth Reached</h4>
              <p className="text-xs text-orange-700 mt-1">
                {nodesAtMaxDepth.length} {nodesAtMaxDepth.length === 1 ? 'document' : 'documents'} at depth level {MAX_DEPTH} 
                (highlighted in orange) may have deeper dependencies not shown. 
                Documents: {nodesAtMaxDepth.map(n => n.document_number).join(', ')}
              </p>
            </div>
          </div>
        </div>
      )}
      
      <div className="h-[600px] w-full border border-gray-300 rounded-lg bg-white">
        <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.5}
        maxZoom={2}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            if (node.data.isCurrent) return '#3B82F6';
            if (node.data.isAtMaxDepth) return '#FEF3C7';
            if (node.data.isCritical) return '#FEE2E2';
            return '#F3F4F6';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
          style={{ background: '#F9FAFB' }}
        />
      </ReactFlow>
      
        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white border border-gray-300 rounded-lg p-3 shadow-lg z-10">
          <h4 className="text-xs font-semibold mb-2 text-gray-700">Legend</h4>
          <div className="space-y-1 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-500 border-2 border-blue-600 rounded"></div>
              <span>Current Document</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-yellow-100 border-2 border-orange-500 rounded"></div>
              <span>⚠️ Max Depth (L{MAX_DEPTH})</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-100 border-2 border-red-500 rounded"></div>
              <span>Critical Dependency</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-gray-100 border-2 border-gray-300 rounded"></div>
              <span>Standard Document</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-0.5 bg-red-500"></div>
              <span>Critical Connection</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-0.5 bg-gray-400"></div>
              <span>Standard Connection</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DependencyGraphView;
