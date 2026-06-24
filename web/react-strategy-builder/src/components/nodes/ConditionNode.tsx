import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { StrategyNodeData } from '../../types/strategy';

const categoryColors: Record<string, { border: string; bg: string; icon: string }> = {
  entry: { border: '#10b981', bg: '#ecfdf5', icon: '🟢' },
  exit: { border: '#ef4444', bg: '#fef2f2', icon: '🔴' },
  filter: { border: '#f59e0b', bg: '#fffbeb', icon: '🟡' },
  risk: { border: '#8b5cf6', bg: '#f5f3ff', icon: '🟣' },
  logic: { border: '#3b82f6', bg: '#eff6ff', icon: '🔵' },
};

interface ConditionNodeProps {
  data: StrategyNodeData;
  selected?: boolean;
}

function ConditionNode({ data, selected }: ConditionNodeProps) {
  const color = categoryColors[data.category || 'entry'] || categoryColors.entry;
  
  return (
    <div
      style={{
        border: `2px solid ${color.border}`,
        background: color.bg,
        borderRadius: '8px',
        padding: '12px',
        minWidth: '180px',
        boxShadow: selected ? `0 0 0 3px ${color.border}40` : '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color.border }} />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
        <span>{color.icon}</span>
        <strong style={{ fontSize: '14px', color: '#1f2937' }}>{data.label}</strong>
      </div>
      
      {data.description && (
        <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
          {data.description}
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} style={{ background: color.border }} />
    </div>
  );
}

export default memo(ConditionNode);
