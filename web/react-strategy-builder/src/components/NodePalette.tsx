import { useState } from 'react';
import { CONDITION_TYPES } from '../config/conditions';

export default function NodePalette() {
  const [activeCategory, setActiveCategory] = useState<string>('entry');
  
  const categories = [
    { key: 'entry', label: '入场条件', color: '#10b981' },
    { key: 'exit', label: '出场条件', color: '#ef4444' },
    { key: 'filter', label: '过滤条件', color: '#f59e0b' },
    { key: 'risk', label: '风控配置', color: '#8b5cf6' },
  ];
  
  const filteredConditions = CONDITION_TYPES.filter(
    (c) => c.category === activeCategory
  );

  const onDragStart = (event: React.DragEvent, conditionType: string) => {
    event.dataTransfer.setData('application/reactflow', 'condition');
    event.dataTransfer.setData('conditionType', conditionType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      style={{
        width: '240px',
        height: '100vh',
        borderRight: '1px solid #e5e7eb',
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>🧩 节点面板</h3>
        <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#6b7280' }}>
          拖拽节点到画布
        </p>
      </div>
      
      {/* Category Tabs */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', padding: '12px' }}>
        {categories.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '12px',
              cursor: 'pointer',
              background: activeCategory === cat.key ? cat.color : '#f3f4f6',
              color: activeCategory === cat.key ? '#fff' : '#374151',
            }}
          >
            {cat.label}
          </button>
        ))}
      </div>
      
      {/* Condition List */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 12px 12px' }}>
        {filteredConditions.map((condition) => (
          <div
            key={condition.type}
            draggable
            onDragStart={(e) => onDragStart(e, condition.type)}
            className="palette-item"
          >
            <div>
              <div style={{ fontWeight: 500, fontSize: '14px' }}>{condition.label}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>{condition.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
