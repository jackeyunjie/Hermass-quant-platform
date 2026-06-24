import type { Node, Edge } from '@xyflow/react';
import type { StrategyNodeData, StrategyDSL, ConditionBlock, RiskConfig, MultiTimeframeConfig, MultiPeriodConfig, BacktestPeriod } from '../types/strategy';

export interface DSLGeneratorOptions {
  multiTimeframe?: MultiTimeframeConfig;
  multiPeriod?: MultiPeriodConfig;
}

export function generateDSL(
  nodes: Node<StrategyNodeData>[],
  _edges: Edge[],
  strategyId: string,
  strategyName: string,
  options: DSLGeneratorOptions = {}
): StrategyDSL {
  const entry: ConditionBlock[] = [];
  const exit: ConditionBlock[] = [];
  const filters: ConditionBlock[] = [];
  let risk: RiskConfig = {
    risk_per_trade: 0.02,
    max_position_pct: 0.20,
    stop_loss_required: true,
  };

  // Process each node based on its category
  for (const node of nodes) {
    const { category, conditionType, params } = node.data;
    
    if (!conditionType || !category) continue;

    const block: ConditionBlock = {
      condition_type: conditionType,
      params: { ...params },
    };

    switch (category) {
      case 'entry':
        entry.push(block);
        break;
      case 'exit':
        block.logic = 'or';
        exit.push(block);
        break;
      case 'filter':
        filters.push(block);
        break;
      case 'risk':
        // Extract risk config from risk node params
        if (params.stop_loss_pct !== undefined) {
          risk = {
            risk_per_trade: params.risk_per_trade || 0.02,
            max_position_pct: params.max_position || 0.20,
            stop_loss_required: true,
          };
        }
        break;
    }
  }

  const dsl: StrategyDSL = {
    strategy_id: strategyId,
    name: strategyName,
    version: 'strategy_dsl_v2',
    entry,
    exit,
    filters,
    risk,
  };

  // Add multi-timeframe config if provided
  if (options.multiTimeframe) {
    dsl.multi_timeframe = options.multiTimeframe;
  }

  // Add multi-period config if provided
  if (options.multiPeriod) {
    dsl.multi_period = options.multiPeriod;
  }

  return dsl;
}

export function validateNodeConnections(nodes: Node<StrategyNodeData>[], edges: Edge[]): string[] {
  const errors: string[] = [];
  
  // Check if there's at least one entry condition
  const hasEntry = nodes.some((node) => node.data.category === 'entry');
  if (!hasEntry) {
    errors.push('策略必须包含至少一个入场条件');
  }
  
  // Check if there's at least one exit condition
  const hasExit = nodes.some((node) => node.data.category === 'exit');
  if (!hasExit) {
    errors.push('策略必须包含至少一个出场条件');
  }
  
  // Check if all condition nodes have required params
  for (const node of nodes) {
    const { conditionType, params, category } = node.data;
    if (!conditionType || category === 'risk') continue;
    
    // Basic param validation based on condition type
    const requiredParams = getRequiredParams(conditionType);
    for (const param of requiredParams) {
      if (params[param] === undefined || params[param] === null || params[param] === '') {
        errors.push(`节点 "${node.data.label}" 缺少必需参数: ${param}`);
      }
    }
  }
  
  // Check for orphaned nodes (no connections)
  const connectedNodeIds = new Set<string>();
  for (const edge of edges) {
    connectedNodeIds.add(edge.source);
    connectedNodeIds.add(edge.target);
  }
  
  for (const node of nodes) {
    if (node.type === 'input') continue; // Skip start node
    if (!connectedNodeIds.has(node.id)) {
      errors.push(`节点 "${node.data.label}" 未连接到策略流程中`);
    }
  }
  
  return errors;
}

function getRequiredParams(conditionType: string): string[] {
  const paramMap: Record<string, string[]> = {
    ma_golden_cross: ['fast_period', 'slow_period'],
    ma_death_cross: ['fast_period', 'slow_period'],
    price_cross_ma: ['timeframe', 'ma_period', 'direction'],
    state_hex_in: ['timeframe', 'values'],
    state_ef_count: ['operator', 'value'],
    volume_ratio: ['lookback', 'operator', 'value'],
    stop_loss_pct: ['value'],
    take_profit_pct: ['value'],
    industry_include: ['values'],
    industry_exclude: ['values'],
    limit_up_filter: ['allow'],
    // SQX Expansion
    rsi_threshold: ['period', 'operator', 'value'],
    macd_cross: ['fast', 'slow', 'signal', 'direction'],
    bollinger_breakout: ['period', 'std_dev', 'direction'],
    ma_bullish_alignment: ['ma_periods'],
    price_above_ma: ['ma_period'],
    atr_trailing_stop: ['atr_period', 'multiplier'],
    exit_after_bars: ['max_bars'],
    indicator_reversal_exit: ['indicator', 'period', 'direction'],
    liquidity_filter: ['min_turnover'],
    volatility_filter: ['atr_period', 'operator', 'threshold_pct'],
    time_filter: [],
    st_new_stock_filter: ['exclude_st'],
    max_position_pct: ['value'],
    max_drawdown_stop: ['value'],
  };
  
  return paramMap[conditionType] || [];
}

// Multi-timeframe helpers
export function createMultiTimeframeConfig(
  timeframes: string[] = ['D1'],
  primary: string = 'D1',
  requireAll: boolean = false
): MultiTimeframeConfig {
  return {
    timeframes,
    primary_timeframe: primary,
    require_all_timeframes: requireAll,
  };
}

// Multi-period helpers
export function createMultiPeriodConfig(
  periods: BacktestPeriod[] = [],
  aggregateMethod: 'concat' | 'average' | 'weighted' = 'concat',
  minPeriods: number = 1
): MultiPeriodConfig {
  return {
    periods,
    aggregate_method: aggregateMethod,
    min_periods_required: minPeriods,
  };
}

// Preset period configurations for common market regimes
export const PRESET_PERIODS = {
  bull_bear_split: [
    { start_date: '2020-01-01', end_date: '2021-12-31', label: '2020-2021 牛市' },
    { start_date: '2022-01-01', end_date: '2024-12-31', label: '2022-2024 震荡' },
  ],
  five_year_split: [
    { start_date: '2020-01-01', end_date: '2020-12-31', label: '2020' },
    { start_date: '2021-01-01', end_date: '2021-12-31', label: '2021' },
    { start_date: '2022-01-01', end_date: '2022-12-31', label: '2022' },
    { start_date: '2023-01-01', end_date: '2023-12-31', label: '2023' },
    { start_date: '2024-01-01', end_date: '2024-12-31', label: '2024' },
  ],
  crisis_test: [
    { start_date: '2020-01-01', end_date: '2020-06-30', label: '2020疫情暴跌' },
    { start_date: '2020-07-01', end_date: '2021-12-31', label: '2020-2021反弹' },
    { start_date: '2022-01-01', end_date: '2022-12-31', label: '2022熊市' },
  ],
};
