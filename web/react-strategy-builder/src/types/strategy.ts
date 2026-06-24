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

// Multi-timeframe configuration
export interface MultiTimeframeConfig {
  timeframes: string[];
  primary_timeframe: string;
  require_all_timeframes: boolean;
}

// Multi-period configuration
export interface BacktestPeriod {
  start_date: string;
  end_date: string;
  label: string;
}

export interface MultiPeriodConfig {
  periods: BacktestPeriod[];
  aggregate_method: 'concat' | 'average' | 'weighted';
  min_periods_required: number;
}

export interface StrategyDSL {
  strategy_id: string;
  name: string;
  version: string;
  entry: ConditionBlock[];
  exit: ConditionBlock[];
  filters: ConditionBlock[];
  risk: RiskConfig;
  multi_timeframe?: MultiTimeframeConfig;
  multi_period?: MultiPeriodConfig;
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

// Multi-timeframe backtest result types
export interface TimeframeResult {
  timeframe: string;
  signal_count: number;
  agreement_rate: number;
  metrics: Record<string, number>;
  status: string;
}

export interface MultiTimeframeBacktestResult {
  primary_timeframe: string;
  overall_metrics: Record<string, number>;
  timeframe_results: TimeframeResult[];
  cross_timeframe_signals: CrossTimeframeSignal[];
  elapsed_seconds: number;
  status: string;
  warnings: string[];
}

export interface CrossTimeframeSignal {
  date: string;
  timeframes: string[];
  symbols: string[];
  timeframe_count: number;
}

// Multi-period backtest result types
export interface PeriodResult {
  label: string;
  start_date: string;
  end_date: string;
  metrics: Record<string, number>;
  trade_count: number;
  status: string;
}

export interface PeriodComparison {
  period_count: number;
  success_count: number;
  failed_count: number;
  best_period?: string;
  best_return?: number;
  worst_period?: string;
  worst_return?: number;
  safest_period?: string;
  safest_drawdown?: number;
  riskiest_period?: string;
  riskiest_drawdown?: number;
  period_summaries: PeriodSummary[];
}

export interface PeriodSummary {
  label: string;
  start_date: string;
  end_date: string;
  total_return: number;
  max_drawdown: number;
  trade_count: number;
  status: string;
}

export interface MultiPeriodBacktestResult {
  overall_metrics: Record<string, number>;
  period_results: PeriodResult[];
  period_comparison: PeriodComparison;
  elapsed_seconds: number;
  status: string;
  warnings: string[];
}
