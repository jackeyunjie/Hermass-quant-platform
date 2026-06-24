import { STRATEGY_TEMPLATES } from '../../config/conditions';

interface TemplateGalleryProps {
  onClose: () => void;
  onSelectTemplate: (nodes: any[], edges: any[]) => void;
}

export default function TemplateGallery({ onClose, onSelectTemplate }: TemplateGalleryProps) {
  return (
    <div className="panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>📋 策略模板</h3>
        <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: '18px' }}>
          ✕
        </button>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
        {STRATEGY_TEMPLATES.map((template) => (
          <div
            key={template.id}
            style={{
              padding: '16px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onClick={() => onSelectTemplate(template.nodes, template.edges)}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#3b82f6';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#e5e7eb';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <h4 style={{ margin: '0 0 8px', fontSize: '15px', fontWeight: 600 }}>
              {template.name}
            </h4>
            <p style={{ margin: 0, fontSize: '13px', color: '#6b7280', lineHeight: 1.5 }}>
              {template.description}
            </p>
            <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {template.nodes
                .filter((n) => n.data.category && n.data.category !== 'risk')
                .map((node, i) => (
                  <span
                    key={i}
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      background:
                        node.data.category === 'entry'
                          ? '#d1fae5'
                          : node.data.category === 'exit'
                          ? '#fee2e2'
                          : '#fef3c7',
                      color:
                        node.data.category === 'entry'
                          ? '#065f46'
                          : node.data.category === 'exit'
                          ? '#991b1b'
                          : '#92400e',
                    }}
                  >
                    {node.data.label}
                  </span>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
