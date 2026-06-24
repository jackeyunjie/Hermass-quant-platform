import { create } from 'zustand';
import type { Node, Edge } from '@xyflow/react';
import type { StrategyNodeData, ValidationResult } from '../types/strategy';

interface StrategyState {
  // Nodes and edges
  nodes: Node<StrategyNodeData>[];
  edges: Edge[];
  selectedNode: string | null;
  
  // Strategy metadata
  strategyId: string;
  strategyName: string;
  
  // Validation
  validationResult: ValidationResult | null;
  isValidating: boolean;
  
  // UI state
  showTemplates: boolean;
  
  // Actions
  setNodes: (nodes: Node<StrategyNodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (node: Node<StrategyNodeData>) => void;
  updateNode: (id: string, data: Partial<StrategyNodeData>) => void;
  removeNode: (id: string) => void;
  addEdge: (edge: Edge) => void;
  removeEdge: (id: string) => void;
  setSelectedNode: (id: string | null) => void;
  setStrategyId: (id: string) => void;
  setStrategyName: (name: string) => void;
  setValidationResult: (result: ValidationResult | null) => void;
  setIsValidating: (isValidating: boolean) => void;
  setShowTemplates: (show: boolean) => void;
  loadTemplate: (nodes: Node<StrategyNodeData>[], edges: Edge[]) => void;
  reset: () => void;
}

const initialNodes: Node<StrategyNodeData>[] = [
  {
    id: 'start',
    type: 'input',
    position: { x: 250, y: 50 },
    data: { label: '策略开始', params: {} },
  },
];

export const useStrategyStore = create<StrategyState>((set) => ({
  nodes: initialNodes,
  edges: [],
  selectedNode: null,
  strategyId: 'strategy_001',
  strategyName: '新策略',
  validationResult: null,
  isValidating: false,
  showTemplates: false,
  
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  
  addNode: (node) => set((state) => ({ 
    nodes: [...state.nodes, node] 
  })),
  
  updateNode: (id, data) => set((state) => ({
    nodes: state.nodes.map((node) =>
      node.id === id ? { ...node, data: { ...node.data, ...data } } : node
    ),
  })),
  
  removeNode: (id) => set((state) => ({
    nodes: state.nodes.filter((node) => node.id !== id),
    edges: state.edges.filter((edge) => edge.source !== id && edge.target !== id),
  })),
  
  addEdge: (edge) => set((state) => ({ 
    edges: [...state.edges, edge] 
  })),
  
  removeEdge: (id) => set((state) => ({
    edges: state.edges.filter((edge) => edge.id !== id),
  })),
  
  setSelectedNode: (id) => set({ selectedNode: id }),
  setStrategyId: (id) => set({ strategyId: id }),
  setStrategyName: (name) => set({ strategyName: name }),
  setValidationResult: (result) => set({ validationResult: result }),
  setIsValidating: (isValidating) => set({ isValidating }),
  setShowTemplates: (show) => set({ showTemplates: show }),
  
  loadTemplate: (nodes, edges) => set({ 
    nodes, 
    edges, 
    selectedNode: null,
    validationResult: null,
  }),
  
  reset: () => set({
    nodes: initialNodes,
    edges: [],
    selectedNode: null,
    strategyId: 'strategy_001',
    strategyName: '新策略',
    validationResult: null,
    isValidating: false,
  }),
}));
