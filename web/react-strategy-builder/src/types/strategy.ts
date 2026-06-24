import type { Node, Edge } from '@xyflow/react';

export interface StrategyNodeData extends Record<string, unknown> {
  label: string;
  conditionType?: string;
  params: Record<string, any>;
  category?: 'entry' | 'exit' | 'filter' | 'risk' | 'logic';
  description?: string;
}

export interface ConditionType {
  type: string;
  label: string;
  category: 'entry' | 'exit' | 'filter' | 'risk';
  description: string;
  params: ParamDefinition[];
}

export interface ParamDefinition {
  name: string;
  label: string;
  type: 'string' | 'number' | 'integer' | 'boolean' | 'select' | 'array';
  required: boolean;
  default?: any;
  options?: { label: string; value: string }[];
  min?: number;
  max?: number;
  description?: string;
}

export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  nodes: Node<StrategyNodeData>[];
  edges: Edge[];
}

export interface ValidationResult {
  passed: boolean;
  level: 'error' | 'warning' | 'info';
  errors: ValidationError[];
  warnings: ValidationError[];
  redLineResult: {
    passed: boolean;
    triggeredRules: string[];
  };
}

export interface ValidationError {
  code: string;
  message: string;
  path?: string;
}

export interface StrategyDSL {
  strategy_id: string;
  name: string;
  version: string;
  entry: ConditionBlock[];
  exit: ConditionBlock[];
  filters: ConditionBlock[];
  risk: RiskConfig;
}

export interface ConditionBlock {
  condition_type: string;
  params: Record<string, any>;
  logic?: 'and' | 'or';
}

export interface RiskConfig {
  risk_per_trade: number;
  max_position_pct: number;
  stop_loss_required: boolean;
}
