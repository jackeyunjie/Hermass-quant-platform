import { useCallback, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Edge,
  type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import ConditionNode from './nodes/ConditionNode';
import NodePalette from './NodePalette';
import PropertyPanel from './PropertyPanel';
import TemplateGallery from './templates/TemplateGallery';
import { useStrategyStore } from '../stores/strategyStore';
import { generateDSL, validateNodeConnections } from '../utils/dslGenerator';
import { CONDITION_TYPES } from '../config/conditions';
import type { StrategyNodeData } from '../types/strategy';

const nodeTypes = {
  condition: ConditionNode,
  input: ConditionNode,
};

export default function FlowCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<StrategyNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  
  const {
    strategyId,
    strategyName,
    setSelectedNode,
    setValidationResult,
    setIsValidating,
    showTemplates,
    setShowTemplates,
  } = useStrategyStore();

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge({ ...connection, type: 'smoothstep' }, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node.id);
  }, [setSelectedNode]);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowInstance) return;

      const type = event.dataTransfer.getData('application/reactflow');
      const conditionType = event.dataTransfer.getData('conditionType');
      
      if (!type || !conditionType) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const conditionDef = CONDITION_TYPES.find((c) => c.type === conditionType);
      if (!conditionDef) return;

      const newNode: Node<StrategyNodeData> = {
        id: `${conditionType}-${Date.now()}`,
        type: 'condition',
        position,
        data: {
          label: conditionDef.label,
          conditionType: conditionDef.type,
          category: conditionDef.category,
          params: conditionDef.params.reduce((acc, param) => {
            acc[param.name] = param.default;
            return acc;
          }, {} as Record<string, any>),
          description: conditionDef.description,
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const handleValidate = useCallback(async () => {
    setIsValidating(true);
    
    // First check node connections
    const connectionErrors = validateNodeConnections(nodes, edges);
    
    if (connectionErrors.length > 0) {
      setValidationResult({
        passed: false,
        level: 'error',
        errors: connectionErrors.map((msg) => ({ code: 'CONNECTION_ERROR', message: msg })),
        warnings: [],
        redLineResult: { passed: false, triggeredRules: [] },
      });
      setIsValidating(false);
      return;
    }

    // Generate DSL
    const dsl = generateDSL(nodes, edges, strategyId, strategyName);
    
    try {
      // Call backend validation API
      const response = await fetch('/api/strategy-lab/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dsl, trace_id: `builder-${Date.now()}` }),
      });
      
      const result = await response.json();
      setValidationResult(result);
    } catch (error) {
      setValidationResult({
        passed: false,
        level: 'error',
        errors: [{ code: 'API_ERROR', message: '验证请求失败: ' + (error as Error).message }],
        warnings: [],
        redLineResult: { passed: false, triggeredRules: [] },
      });
    }
    
    setIsValidating(false);
  }, [nodes, edges, strategyId, strategyName, setValidationResult, setIsValidating]);

  const handleGenerateDSL = useCallback(() => {
    const dsl = generateDSL(nodes, edges, strategyId, strategyName);
    console.log('Generated DSL:', dsl);
    alert('DSL 已生成，请查看控制台');
  }, [nodes, edges, strategyId, strategyName]);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      {/* Left Panel - Node Palette */}
      <NodePalette />

      {/* Center - Flow Canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          style={{ background: '#f9fafb' }}
        >
          <Background gap={12} size={1} />
          <Controls />
          <MiniMap
            nodeStrokeWidth={3}
            zoomable
            pannable
          />
        </ReactFlow>

        {/* Top Toolbar */}
        <div
          style={{
            position: 'absolute',
            top: '16px',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '8px',
            zIndex: 10,
          }}
        >
          <button className="btn btn-secondary" onClick={() => setShowTemplates(!showTemplates)}>
            📋 策略模板
          </button>
          <button className="btn btn-primary" onClick={handleValidate}>
            ✅ 验证策略
          </button>
          <button className="btn btn-success" onClick={handleGenerateDSL}>
            🚀 生成DSL
          </button>
        </div>

        {/* Template Gallery */}
        {showTemplates && (
          <div
            style={{
              position: 'absolute',
              top: '60px',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 20,
              width: '600px',
              maxHeight: '400px',
              overflow: 'auto',
            }}
          >
            <TemplateGallery
              onClose={() => setShowTemplates(false)}
              onSelectTemplate={(templateNodes, templateEdges) => {
                setNodes(templateNodes);
                setEdges(templateEdges);
                setShowTemplates(false);
              }}
            />
          </div>
        )}
      </div>

      {/* Right Panel - Property Panel */}
      <PropertyPanel />
    </div>
  );
}
