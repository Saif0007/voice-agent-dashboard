import React, { useState } from 'react';
import './App.css';
import AgentConfiguration from './components/AgentConfiguration';
import CallTrigger from './components/CallTrigger';
import CallResults from './components/CallResults';

function App() {
  const [agentConfig, setAgentConfig] = useState({
    prompt: '',
    logic: ''
  });

  const [callResults, setCallResults] = useState(null);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Voice Agent Dashboard</h1>
      </header>
      <main className="App-main">
        <div className="dashboard-container">
          <div className="config-section">
            <AgentConfiguration
              config={agentConfig}
              setConfig={setAgentConfig}
            />
          </div>
          <div className="call-section">
            <CallTrigger
              agentConfig={agentConfig}
              setCallResults={setCallResults}
            />
          </div>
        </div>
        {callResults && (
          <div className="results-container">
            <CallResults
              callResults={callResults}
              setCallResults={setCallResults}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
