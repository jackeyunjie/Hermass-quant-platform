import type { ConditionType, StrategyTemplate } from '../types/strategy';

export const CONDITION_TYPES: ConditionType[] = [
  // Entry conditions
  {
    type: 'ma_golden_cross',
    label: '均线金叉',
    category: 'entry',
    description: '快线上穿慢线（金叉）',
    params: [
      { name: 'fast_period', label: '快线周期', type: 'integer', required: true, default: 5, min: 1, max: 252 },
      { name: 'slow_period', label: '慢线周期', type: 'integer', required: true, default: 20, min: 1, max: 252 },
    ],
  },
  {
    type: 'price_cross_ma',
    label: '价格突破均线',
    category: 'entry',
    description: '价格突破指定均线',
    params: [
      { name: 'timeframe', label: '时间周期', type: 'select', required: true, default: 'D1', options: [{ label: '日线', value: 'D1' }, { label: '周线', value: 'W1' }, { label: '月线', value: 'MN1' }] },
      { name: 'ma_period', label: '均线周期', type: 'integer', required: true, default: 20, min: 1, max: 252 },
      { name: 'direction', label: '方向', type: 'select', required: true, default: 'above', options: [{ label: '上穿', value: 'above' }, { label: '跌破', value: 'below' }] },
    ],
  },
  {
    type: 'state_hex_in',
    label: '状态值匹配',
    category: 'entry',
    description: '状态值在指定集合中',
    params: [
      { name: 'timeframe', label: '时间周期', type: 'select', required: true, default: 'D1', options: [{ label: '日线', value: 'D1' }, { label: '周线', value: 'W1' }, { label: '月线', value: 'MN1' }] },
      { name: 'values', label: '状态值', type: 'array', required: true, default: ['0x01'], description: '逗号分隔的状态值' },
    ],
  },
  {
    type: 'state_ef_count',
    label: 'EF数量条件',
    category: 'entry',
    description: 'EF数量满足条件',
    params: [
      { name: 'operator', label: '运算符', type: 'select', required: true, default: '>=', options: [{ label: '>=', value: '>=' }, { label: '>', value: '>' }, { label: '<=', value: '<=' }, { label: '<', value: '<' }] },
      { name: 'value', label: '阈值', type: 'integer', required: true, default: 3, min: 0, max: 10 },
    ],
  },
  {
    type: 'volume_ratio',
    label: '成交量放大',
    category: 'entry',
    description: '成交量相对均值放大',
    params: [
      { name: 'lookback', label: '回看周期', type: 'integer', required: true, default: 5, min: 1, max: 60 },
      { name: 'operator', label: '运算符', type: 'select', required: true, default: '>', options: [{ label: '>', value: '>' }, { label: '>=', value: '>=' }] },
      { name: 'value', label: '倍数', type: 'number', required: true, default: 2, min: 0 },
    ],
  },
  // Exit conditions
  {
    type: 'ma_death_cross',
    label: '均线死叉',
    category: 'exit',
    description: '快线下穿慢线（死叉）',
    params: [
      { name: 'fast_period', label: '快线周期', type: 'integer', required: true, default: 5, min: 1, max: 252 },
      { name: 'slow_period', label: '慢线周期', type: 'integer', required: true, default: 20, min: 1, max: 252 },
    ],
  },
  {
    type: 'stop_loss_pct',
    label: '止损百分比',
    category: 'exit',
    description: '亏损达到指定百分比时出场',
    params: [
      { name: 'value', label: '止损比例(%)', type: 'number', required: true, default: 0.08, min: 0.01, max: 0.5, description: '例如 0.08 表示 8%' },
    ],
  },
  {
    type: 'take_profit_pct',
    label: '止盈百分比',
    category: 'exit',
    description: '盈利达到指定百分比时出场',
    params: [
      { name: 'value', label: '止盈比例(%)', type: 'number', required: true, default: 0.15, min: 0.01, max: 1.0, description: '例如 0.15 表示 15%' },
    ],
  },
  // Filter conditions
  {
    type: 'industry_include',
    label: '行业包含',
    category: 'filter',
    description: '仅包含指定行业的股票',
    params: [
      { name: 'values', label: '行业列表', type: 'array', required: true, default: ['电子'], description: '逗号分隔的行业名称' },
    ],
  },
  {
    type: 'industry_exclude',
    label: '行业排除',
    category: 'filter',
    description: '排除指定行业的股票',
    params: [
      { name: 'values', label: '行业列表', type: 'array', required: true, default: ['银行'], description: '逗号分隔的行业名称' },
    ],
  },
  {
    type: 'limit_up_filter',
    label: '涨停过滤',
    category: 'filter',
    description: '是否包含涨停股票',
    params: [
      { name: 'allow', label: '允许涨停', type: 'boolean', required: true, default: false },
    ],
  },
];

export const STRATEGY_TEMPLATES: StrategyTemplate[] = [
  {
    id: 'ma_cross',
    name: '双均线交叉策略',
    description: 'MA5上穿MA20买入，MA5下穿MA20卖出，止损8%',
    nodes: [
      {
        id: 'entry-1',
        type: 'condition',
        position: { x: 250, y: 100 },
        data: {
          label: 'MA5上穿MA20',
          conditionType: 'ma_golden_cross',
          category: 'entry',
          params: { fast_period: 5, slow_period: 20 },
          description: '快线周期: 5, 慢线周期: 20',
        },
      },
      {
        id: 'exit-1',
        type: 'condition',
        position: { x: 250, y: 300 },
        data: {
          label: 'MA5下穿MA20',
          conditionType: 'ma_death_cross',
          category: 'exit',
          params: { fast_period: 5, slow_period: 20 },
          description: '快线周期: 5, 慢线周期: 20',
        },
      },
      {
        id: 'risk-1',
        type: 'risk',
        position: { x: 450, y: 200 },
        data: {
          label: '风控配置',
          category: 'risk',
          params: { stop_loss_pct: 0.08, max_position: 0.2 },
          description: '止损8%, 仓位20%',
        },
      },
    ],
    edges: [
      { id: 'e1', source: 'entry-1', target: 'exit-1', type: 'smoothstep' },
    ],
  },
  {
    id: 'price_breakout',
    name: '价格突破策略',
    description: '价格上穿MA20买入，跌破MA10卖出，止损5%',
    nodes: [
      {
        id: 'entry-1',
        type: 'condition',
        position: { x: 250, y: 100 },
        data: {
          label: '价格上穿MA20',
          conditionType: 'price_cross_ma',
          category: 'entry',
          params: { timeframe: 'D1', ma_period: 20, direction: 'above' },
          description: '日线, 均线周期: 20, 方向: 上穿',
        },
      },
      {
        id: 'exit-1',
        type: 'condition',
        position: { x: 250, y: 300 },
        data: {
          label: '价格跌破MA10',
          conditionType: 'price_cross_ma',
          category: 'exit',
          params: { timeframe: 'D1', ma_period: 10, direction: 'below' },
          description: '日线, 均线周期: 10, 方向: 跌破',
        },
      },
      {
        id: 'risk-1',
        type: 'risk',
        position: { x: 450, y: 200 },
        data: {
          label: '风控配置',
          category: 'risk',
          params: { stop_loss_pct: 0.05, max_position: 0.2 },
          description: '止损5%, 仓位20%',
        },
      },
    ],
    edges: [
      { id: 'e1', source: 'entry-1', target: 'exit-1', type: 'smoothstep' },
    ],
  },
  {
    id: 'volume_breakout',
    name: '放量突破策略',
    description: '成交量放大到5日均量2倍以上，且价格上穿MA20，止损8%',
    nodes: [
      {
        id: 'entry-1',
        type: 'condition',
        position: { x: 100, y: 100 },
        data: {
          label: '成交量放大2倍',
          conditionType: 'volume_ratio',
          category: 'entry',
          params: { lookback: 5, operator: '>', value: 2 },
          description: '回看5日, 大于2倍',
        },
      },
      {
        id: 'entry-2',
        type: 'condition',
        position: { x: 350, y: 100 },
        data: {
          label: '价格上穿MA20',
          conditionType: 'price_cross_ma',
          category: 'entry',
          params: { timeframe: 'D1', ma_period: 20, direction: 'above' },
          description: '日线, 均线20, 上穿',
        },
      },
      {
        id: 'exit-1',
        type: 'condition',
        position: { x: 250, y: 300 },
        data: {
          label: '止损8%',
          conditionType: 'stop_loss_pct',
          category: 'exit',
          params: { value: 0.08 },
          description: '止损比例: 8%',
        },
      },
      {
        id: 'risk-1',
        type: 'risk',
        position: { x: 500, y: 200 },
        data: {
          label: '风控配置',
          category: 'risk',
          params: { stop_loss_pct: 0.08, max_position: 0.2 },
          description: '止损8%, 仓位20%',
        },
      },
    ],
    edges: [
      { id: 'e1', source: 'entry-1', target: 'entry-2', type: 'smoothstep' },
      { id: 'e2', source: 'entry-2', target: 'exit-1', type: 'smoothstep' },
    ],
  },
];
