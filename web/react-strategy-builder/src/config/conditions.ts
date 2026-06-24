import type { ConditionType, StrategyTemplate } from '../types/strategy';

export const CONDITION_TYPES: ConditionType[] = [
  // Entry conditions - Moving Average
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
    type: 'ma_death_cross',
    label: '均线死叉',
    category: 'entry',
    description: '快线下穿慢线（死叉）- 可用于做空或多头出场',
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
    type: 'ma_bullish_alignment',
    label: '均线多头排列',
    category: 'entry',
    description: '短期均线在长期均线上方，形成多头排列',
    params: [
      { name: 'ma_periods', label: '均线周期', type: 'array', required: true, default: [5, 10, 20], description: '如 [5,10,20] 表示 MA5>MA10>MA20' },
    ],
  },
  {
    type: 'price_above_ma',
    label: '价格在均线上方',
    category: 'entry',
    description: '价格持续在均线上方运行',
    params: [
      { name: 'ma_period', label: '均线周期', type: 'integer', required: true, default: 20, min: 1, max: 252 },
      { name: 'consecutive_bars', label: '连续K线数', type: 'integer', required: false, default: 1, min: 1, max: 20, description: '价格连续在均线上方运行的K线数量' },
    ],
  },
  // Entry conditions - Oscillators
  {
    type: 'rsi_threshold',
    label: 'RSI阈值',
    category: 'entry',
    description: 'RSI指标超过或低于阈值（如超卖<30，超买>70）',
    params: [
      { name: 'period', label: 'RSI周期', type: 'integer', required: true, default: 14, min: 2, max: 60 },
      { name: 'operator', label: '运算符', type: 'select', required: true, default: '<', options: [{ label: '>', value: '>' }, { label: '<', value: '<' }, { label: '>=', value: '>=' }, { label: '<=', value: '<=' }] },
      { name: 'value', label: '阈值', type: 'number', required: true, default: 30, min: 0, max: 100, description: 'RSI阈值 (0-100)' },
    ],
  },
  {
    type: 'macd_cross',
    label: 'MACD交叉',
    category: 'entry',
    description: 'MACD线与信号线交叉',
    params: [
      { name: 'fast', label: '快线周期', type: 'integer', required: true, default: 12, min: 2, max: 60 },
      { name: 'slow', label: '慢线周期', type: 'integer', required: true, default: 26, min: 5, max: 120 },
      { name: 'signal', label: '信号线周期', type: 'integer', required: true, default: 9, min: 2, max: 60 },
      { name: 'direction', label: '方向', type: 'select', required: true, default: 'bullish', options: [{ label: '金叉(看多)', value: 'bullish' }, { label: '死叉(看空)', value: 'bearish' }] },
    ],
  },
  {
    type: 'bollinger_breakout',
    label: '布林带突破',
    category: 'entry',
    description: '价格突破布林带上轨或下轨',
    params: [
      { name: 'period', label: '布林带周期', type: 'integer', required: true, default: 20, min: 5, max: 60 },
      { name: 'std_dev', label: '标准差倍数', type: 'number', required: true, default: 2.0, min: 0.5, max: 5.0 },
      { name: 'direction', label: '突破方向', type: 'select', required: true, default: 'upper', options: [{ label: '突破上轨', value: 'upper' }, { label: '突破下轨', value: 'lower' }] },
    ],
  },
  // Entry conditions - State/Volume
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
  {
    type: 'atr_trailing_stop',
    label: 'ATR追踪止损',
    category: 'exit',
    description: '基于ATR的动态追踪止损（Chandelier风格）',
    params: [
      { name: 'atr_period', label: 'ATR周期', type: 'integer', required: true, default: 14, min: 5, max: 60 },
      { name: 'multiplier', label: 'ATR倍数', type: 'number', required: true, default: 2.0, min: 0.5, max: 5.0, description: '止损距离 = 最高价 - ATR * 倍数' },
    ],
  },
  {
    type: 'exit_after_bars',
    label: '时间出场',
    category: 'exit',
    description: '持仓N根K线后强制出场（时间止损）',
    params: [
      { name: 'max_bars', label: '最大持仓K线数', type: 'integer', required: true, default: 20, min: 1, max: 252, description: '例如 20 表示持仓20天后强制出场' },
    ],
  },
  {
    type: 'indicator_reversal_exit',
    label: '指标反转出场',
    category: 'exit',
    description: '指标从极端区域反转时出场',
    params: [
      { name: 'indicator', label: '指标', type: 'select', required: true, default: 'rsi', options: [{ label: 'RSI', value: 'rsi' }, { label: 'MACD', value: 'macd' }, { label: 'CCI', value: 'cci' }] },
      { name: 'period', label: '周期', type: 'integer', required: true, default: 14, min: 2, max: 60 },
      { name: 'direction', label: '反转方向', type: 'select', required: true, default: 'overbought', options: [{ label: '从超买区回落', value: 'overbought' }, { label: '从超卖区回升', value: 'oversold' }] },
    ],
  },
  {
    type: 'max_drawdown_stop',
    label: '最大回撤止损',
    category: 'exit',
    description: '组合回撤超过阈值时全部平仓（紧急风控）',
    params: [
      { name: 'value', label: '最大回撤比例(%)', type: 'number', required: true, default: 0.10, min: 0.01, max: 0.5, description: '例如 0.10 表示回撤10%时全部平仓' },
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
  {
    type: 'liquidity_filter',
    label: '流动性过滤',
    category: 'filter',
    description: '过滤日均成交额过低的股票',
    params: [
      { name: 'min_turnover', label: '最小成交额(万元)', type: 'number', required: true, default: 1000, min: 100, max: 100000, description: '例如 1000 表示日均成交额需大于1000万元' },
    ],
  },
  {
    type: 'volatility_filter',
    label: '波动率过滤',
    category: 'filter',
    description: '根据ATR波动率过滤股票',
    params: [
      { name: 'atr_period', label: 'ATR周期', type: 'integer', required: true, default: 14, min: 5, max: 60 },
      { name: 'operator', label: '运算符', type: 'select', required: true, default: '>', options: [{ label: '>', value: '>' }, { label: '<', value: '<' }, { label: '>=', value: '>=' }, { label: '<=', value: '<=' }] },
      { name: 'threshold_pct', label: '波动率阈值(%)', type: 'number', required: true, default: 0.02, min: 0.001, max: 0.5, description: 'ATR/收盘价 的比例阈值' },
    ],
  },
  {
    type: 'time_filter',
    label: '时间过滤',
    category: 'filter',
    description: '按交易时间窗口过滤（月份、星期几）',
    params: [
      { name: 'month_range', label: '允许月份', type: 'array', required: false, default: [], description: '如 [3,4,5] 表示仅3-5月交易' },
      { name: 'day_of_week', label: '允许星期', type: 'array', required: false, default: [], description: '如 [1,2,3,4,5] 表示周一到周五' },
      { name: 'exclude_holidays', label: '排除节假日', type: 'boolean', required: false, default: true },
    ],
  },
  {
    type: 'st_new_stock_filter',
    label: 'ST新股过滤',
    category: 'filter',
    description: '排除ST股票和新股',
    params: [
      { name: 'exclude_st', label: '排除ST', type: 'boolean', required: true, default: true },
      { name: 'max_listing_days', label: '新股过滤天数', type: 'integer', required: false, default: 60, min: 0, max: 365, description: '排除上市N天内的股票' },
    ],
  },
  // Risk / Money Management
  {
    type: 'max_position_pct',
    label: '最大仓位限制',
    category: 'filter',
    description: '单只股票最大仓位比例（红线强制）',
    params: [
      { name: 'value', label: '最大仓位(%)', type: 'number', required: true, default: 0.20, min: 0.01, max: 1.0, description: '例如 0.20 表示单票最多20%仓位' },
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
    id: 'rsi_oversold',
    name: 'RSI超卖反弹策略',
    description: 'RSI<30超卖买入，RSI>70超买卖出，止损5%，止盈15%',
    nodes: [
      {
        id: 'entry-1',
        type: 'condition',
        position: { x: 250, y: 100 },
        data: {
          label: 'RSI<30超卖',
          conditionType: 'rsi_threshold',
          category: 'entry',
          params: { period: 14, operator: '<', value: 30 },
          description: 'RSI14 低于 30',
        },
      },
      {
        id: 'exit-1',
        type: 'condition',
        position: { x: 250, y: 300 },
        data: {
          label: 'RSI>70超买',
          conditionType: 'indicator_reversal_exit',
          category: 'exit',
          params: { indicator: 'rsi', period: 14, direction: 'overbought' },
          description: 'RSI从超买区回落',
        },
      },
      {
        id: 'risk-1',
        type: 'risk',
        position: { x: 450, y: 200 },
        data: {
          label: '风控配置',
          category: 'risk',
          params: { stop_loss_pct: 0.05, take_profit_pct: 0.15, max_position: 0.2 },
          description: '止损5%, 止盈15%, 仓位20%',
        },
      },
    ],
    edges: [
      { id: 'e1', source: 'entry-1', target: 'exit-1', type: 'smoothstep' },
    ],
  },
  {
    id: 'macd_bollinger',
    name: 'MACD+布林带策略',
    description: 'MACD金叉且价格突破布林带上轨买入，MACD死叉卖出，ATR追踪止损',
    nodes: [
      {
        id: 'entry-1',
        type: 'condition',
        position: { x: 100, y: 100 },
        data: {
          label: 'MACD金叉',
          conditionType: 'macd_cross',
          category: 'entry',
          params: { fast: 12, slow: 26, signal: 9, direction: 'bullish' },
          description: 'MACD12,26,9 金叉',
        },
      },
      {
        id: 'entry-2',
        type: 'condition',
        position: { x: 350, y: 100 },
        data: {
          label: '突破布林带上轨',
          conditionType: 'bollinger_breakout',
          category: 'entry',
          params: { period: 20, std_dev: 2, direction: 'upper' },
          description: '布林带20,2 突破上轨',
        },
      },
      {
        id: 'exit-1',
        type: 'condition',
        position: { x: 250, y: 300 },
        data: {
          label: 'MACD死叉',
          conditionType: 'macd_cross',
          category: 'exit',
          params: { fast: 12, slow: 26, signal: 9, direction: 'bearish' },
          description: 'MACD12,26,9 死叉',
        },
      },
      {
        id: 'risk-1',
        type: 'risk',
        position: { x: 500, y: 200 },
        data: {
          label: '风控配置',
          category: 'risk',
          params: { atr_trailing_stop: { atr_period: 14, multiplier: 2 }, max_position: 0.2 },
          description: 'ATR14追踪止损, 仓位20%',
        },
      },
    ],
    edges: [
      { id: 'e1', source: 'entry-1', target: 'entry-2', type: 'smoothstep' },
      { id: 'e2', source: 'entry-2', target: 'exit-1', type: 'smoothstep' },
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
  {
    id: 'multi_ma_trend',
    name: '均线趋势跟踪策略',
    description: 'MA5>MA10>MA20多头排列，价格回踩MA10后上涨买入，ATR追踪止损',
    nodes: [
      {
        id: 'entry-1',
        type: 'condition',
        position: { x: 100, y: 100 },
        data: {
          label: 'MA多头排列',
          conditionType: 'ma_bullish_alignment',
          category: 'entry',
          params: { ma_periods: [5, 10, 20] },
          description: 'MA5>MA10>MA20',
        },
      },
      {
        id: 'entry-2',
        type: 'condition',
        position: { x: 350, y: 100 },
        data: {
          label: '价格在MA10上方3天',
          conditionType: 'price_above_ma',
          category: 'entry',
          params: { ma_period: 10, consecutive_bars: 3 },
          description: '价格连续3天在MA10上方',
        },
      },
      {
        id: 'exit-1',
        type: 'condition',
        position: { x: 250, y: 300 },
        data: {
          label: 'ATR追踪止损',
          conditionType: 'atr_trailing_stop',
          category: 'exit',
          params: { atr_period: 14, multiplier: 2 },
          description: 'ATR14, 2倍',
        },
      },
      {
        id: 'filter-1',
        type: 'condition',
        position: { x: 500, y: 50 },
        data: {
          label: '排除ST新股',
          conditionType: 'st_new_stock_filter',
          category: 'filter',
          params: { exclude_st: true, max_listing_days: 60 },
          description: '排除ST和上市60天内股票',
        },
      },
      {
        id: 'risk-1',
        type: 'risk',
        position: { x: 500, y: 250 },
        data: {
          label: '风控配置',
          category: 'risk',
          params: { max_position_pct: 0.2, max_drawdown_stop: 0.1 },
          description: '仓位20%, 最大回撤10%',
        },
      },
    ],
    edges: [
      { id: 'e1', source: 'filter-1', target: 'entry-1', type: 'smoothstep' },
      { id: 'e2', source: 'entry-1', target: 'entry-2', type: 'smoothstep' },
      { id: 'e3', source: 'entry-2', target: 'exit-1', type: 'smoothstep' },
    ],
  },
];
