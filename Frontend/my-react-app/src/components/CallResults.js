import React, { useState } from 'react';
import WebCallInterface from './WebCallInterface';

const CallResults = ({ callResults, setCallResults }) => {
  const [expandedTokens, setExpandedTokens] = useState({});

  const clearResults = () => {
    setCallResults(null);
  };

  const toggleTokenExpansion = (key) => {
    setExpandedTokens(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const formatValue = (key, value) => {
    if (typeof value !== 'string') return value;

    // Handle long tokens (like access tokens)
    if (key.toLowerCase().includes('token') && value.length > 40) {
      const isExpanded = expandedTokens[key];
      const truncated = value.substring(0, 40) + '...';

      return (
        <div>
          <span className="token-value">
            {isExpanded ? value : truncated}
          </span>
          <button
            className="toggle-token-btn"
            onClick={() => toggleTokenExpansion(key)}
          >
            {isExpanded ? 'Hide' : 'Show Full'}
          </button>
        </div>
      );
    }

    return value;
  };

  return (
    <div className="call-results-card">
      <div className="call-results-header">
        <h2>Call Results</h2>
        <button onClick={clearResults} className="clear-results-btn">
          Clear Results
        </button>
      </div>

      <div className="results-summary">
        <div className="result-header">
          <span className="call-status">Status: {callResults.status}</span>
          <span className="call-duration">Duration: {callResults.duration}</span>
          <span className="call-time">Completed: {new Date(callResults.timestamp).toLocaleString()}</span>
        </div>
      </div>

      <div className="key-information">
        <h4>Key Information Collected</h4>
        <div className="info-grid">
          {Object.entries(callResults.keyInformation).map(([key, value]) => (
            <div key={key} className="info-item">
              <span className="info-key">{key}:</span>
              <span className="info-value">{formatValue(key, value)}</span>
            </div>
          ))}
        </div>
      </div>

      {callResults.access_token && (
        <WebCallInterface
          accessToken={callResults.access_token}
          callId={callResults.callId}
          onCallEnd={() => {
            console.log('Web call ended');
            // Optionally refresh call results after web call ends
          }}
        />
      )}

      <div className="transcript-section">
        <h4>Full Call Transcript</h4>
        <div className="transcript">
          {callResults.transcript.map((entry, index) => (
            <div key={index} className={`transcript-entry ${entry.speaker.toLowerCase()}`}>
              <span className="speaker">{entry.speaker}:</span>
              <span className="message">{entry.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CallResults;