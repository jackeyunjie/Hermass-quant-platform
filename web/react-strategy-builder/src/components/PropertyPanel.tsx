import { useStrategyStore } from '../stores/strategyStore';
import { CONDITION_TYPES } from '../config/conditions';
import type { ParamDefinition } from '../types/strategy';

export default function PropertyPanel() {
  const { nodes, selectedNode, updateNode, validationResult } = useStrategyStore();
  
  const selectedNodeData = nodes.find((n) => n.id === selectedNode)?.data;
  const conditionDef = selectedNodeData?.conditionType
    ? CONDITION_TYPES.find((c) => c.type === selectedNodeData.conditionType)
    : null;

  const handleParamChange = (paramName: string, value: any) => {
    if (!selectedNode) return;
    
    const newParams = { ...selectedNodeData?.params, [paramName]: value };
    updateNode(selectedNode, { params: newParams });
  };

  const renderParamInput = (param: ParamDefinition) => {
    const value = selectedNodeData?.params?.[param.name] ?? param.default;
    
    switch (param.type) {
      case 'select':
        return (
          <select
            className="form-select"
            value={value}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
          >
            {param.options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );
      
      case 'boolean':
        return (
          <select
            className="form-select"
            value={String(value)}
            onChange={(e) => handleParamChange(param.name, e.target.value === 'true')}
          >
            <option value="true">是</option>
            <option value="false">否</option>
          </select>
        );
      
      case 'array':
        return (
          <input
            type="text"
            className="form-input"
            value={Array.isArray(value) ? value.join(',') : value}
            onChange={(e) => {
              const arr = e.target.value.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
              handleParamChange(param.name, arr);
            }}
            placeholder={param.description}
          />
        );
      
      case 'number':
      case 'integer':
        return (
          <input
            type="number"
            className="form-input"
            value={value}
            min={param.min}
            max={param.max}
            step={param.type === 'number' ? '0.01' : '1'}
            onChange={(e) => {
              const val = param.type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value);
              handleParamChange(param.name, val);
            }}
          />
        );
      
      default:
        return (
          <input
            type="text"
            className="form-input"
            value={value}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
          />
        );
    }
  };

  return (
    <div className="property-panel">
      <div style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>⚙️ 属性面板</h3>
      </div>
      
      {selectedNode && selectedNodeData ? (
        <div style={{ padding: '16px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">节点名称</label>
            <input
              type="text"
              className="form-input"
              value={selectedNodeData.label}
              onChange={(e) => updateNode(selectedNode, { label: e.target.value })}
            />
          </div>
          
          {conditionDef && (
            <>
              <div style={{ marginBottom: '16px' }}>
                <label className="form-label">条件类型</label>
                <div style={{ padding: '8px', background: '#f3f4f6', borderRadius: '6px', fontSize: '14px' }}>
                  {conditionDef.label}
                </div>
              </div>
              
              <div style={{ marginBottom: '16px' }}>
                <label className="form-label">描述</label>
                <div style={{ fontSize: '13px', color: '#6b7280' }}>
                  {conditionDef.description}
                </div>
              </div>
              
              <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>参数配置</h4>
              
              {conditionDef.params.map((param) => (
                <div key={param.name} className="form-group">
                  <label className="form-label">
                    {param.label}
                    {param.required && <span style={{ color: '#ef4444' }}>*</span>}
                  </label>
                  {renderParamInput(param)}
                  {param.description && (
                    <small style={{ color: '#9ca3af', fontSize: '12px' }}>
                      {param.description}
                    </small>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      ) : (
        <div style={{ padding: '16px', color: '#6b7280', textAlign: 'center' }}>
          <p>选择一个节点以编辑属性</p>
        </div>
      )}
      
      {/* Validation Results */}
      {validationResult && (
        <div style={{ padding: '16px', borderTop: '1px solid #e5e7eb' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>
            验证结果
          </h4>
          
          <div className={`validation-badge ${validationResult.passed ? 'success' : 'error'}`}>
            {validationResult.passed ? '✅ 通过' : '❌ 未通过'}
          </div>
          
          {validationResult.errors.length > 0 && (
            <div style={{ marginTop: '8px' }}>
              <strong style={{ fontSize: '13px', color: '#ef4444' }}>错误:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: '16px', fontSize: '12px' }}>
                {validationResult.errors.map((err, i) => (
                  <li key={i} style={{ color: '#ef4444', marginBottom: '4px' }}>
                    {err.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {validationResult.warnings.length > 0 && (
            <div style={{ marginTop: '8px' }}>
              <strong style={{ fontSize: '13px', color: '#f59e0b' }}>警告:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: '16px', fontSize: '12px' }}>
                {validationResult.warnings.map((warn, i) => (
                  <li key={i} style={{ color: '#f59e0b', marginBottom: '4px' }}>
                    {warn.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {!validationResult.redLineResult.passed && (
            <div style={{ marginTop: '8px' }}>
              <strong style={{ fontSize: '13px', color: '#ef4444' }}>红线检查:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: '16px', fontSize: '12px' }}>
                {validationResult.redLineResult.triggeredRules.map((rule, i) => (
                  <li key={i} style={{ color: '#ef4444' }}>
                    {rule === 'RL_EXIT_MUST_HAVE_STOP_LOSS' ? '缺少止损条件' : rule}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
