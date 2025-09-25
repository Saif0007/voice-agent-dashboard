import React from 'react';

const AgentConfiguration = ({ config, setConfig }) => {
  const handlePromptChange = (e) => {
    setConfig(prev => ({
      ...prev,
      prompt: e.target.value
    }));
  };

  const handleLogicChange = (e) => {
    setConfig(prev => ({
      ...prev,
      logic: e.target.value
    }));
  };

  return (
    <div className="agent-config">
      <h2>Agent Configuration</h2>
      <div className="config-form">
        <div className="form-group">
          <label htmlFor="agent-prompt">Agent Prompt:</label>
          <textarea
            id="agent-prompt"
            value={config.prompt}
            onChange={handlePromptChange}
            placeholder="Define the prompts that guide the agent's conversations..."
            rows={6}
            className="config-textarea"
          />
        </div>
        <div className="form-group">
          <label htmlFor="agent-logic">Conversation Logic:</label>
          <textarea
            id="agent-logic"
            value={config.logic}
            onChange={handleLogicChange}
            placeholder="Define the logic and flow for agent conversations..."
            rows={6}
            className="config-textarea"
          />
        </div>
        <div className="config-status">
          <span className={config.prompt && config.logic ? 'status-ready' : 'status-pending'}>
            {config.prompt && config.logic ? '✓ Configuration Ready' : '⚠ Configuration Incomplete'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default AgentConfiguration;