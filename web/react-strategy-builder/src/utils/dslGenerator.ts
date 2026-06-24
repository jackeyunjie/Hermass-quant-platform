import type { Node, Edge } from '@xyflow/react';
import type { StrategyNodeData, StrategyDSL, ConditionBlock, RiskConfig } from '../types/strategy';

export function generateDSL(
  nodes: Node<StrategyNodeData>[],
  _edges: Edge[],
  strategyId: string,
  strategyName: string
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

  return {
    strategy_id: strategyId,
    name: strategyName,
    version: 'strategy_dsl_v2',
    entry,
    exit,
    filters,
    risk,
  };
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
  };
  
  return paramMap[conditionType] || [];
}
