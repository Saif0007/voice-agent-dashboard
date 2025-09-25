import React, { useState, useEffect, useRef } from 'react';

const WebCallInterface = ({ accessToken, callId, onCallEnd }) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [callStatus, setCallStatus] = useState('ready');
  const [error, setError] = useState(null);
  const retellWebClientRef = useRef(null);

  useEffect(() => {
    let scriptElement = null;

    // Load Retell Web SDK
    const loadRetellSDK = () => {
      // Check if SDK is already loaded
      if (window.RetellWebClient) {
        console.log('Retell SDK already loaded');
        initializeRetellClient();
        return;
      }

      // Check if script is already being loaded
      const existingScript = document.querySelector('script[src*="retell-client-js-sdk"]');
      if (existingScript) {
        console.log('Retell SDK script already exists, waiting for load...');
        existingScript.addEventListener('load', () => {
          if (window.RetellWebClient) {
            initializeRetellClient();
          } else {
            setError('Retell SDK loaded but RetellWebClient not found');
          }
        });
        return;
      }

      console.log('Loading Retell SDK...');
      scriptElement = document.createElement('script');
      scriptElement.src = 'https://cdn.jsdelivr.net/npm/retell-client-js-sdk@2.0.7/dist/web/index.js';
      scriptElement.async = true;

      scriptElement.onload = () => {
        console.log('Retell SDK script loaded');
        // Give it a moment to initialize
        setTimeout(() => {
          if (window.RetellWebClient) {
            console.log('RetellWebClient is available');
            initializeRetellClient();
          } else {
            console.error('RetellWebClient not found after script load');
            setError('Failed to load Retell SDK - RetellWebClient not available');
          }
        }, 100);
      };

      scriptElement.onerror = (e) => {
        console.error('Failed to load Retell SDK script:', e);
        setError('Failed to load Retell SDK script');
      };

      document.head.appendChild(scriptElement);
    };

    const initializeRetellClient = () => {
      try {
        console.log('Initializing Retell client...');

        if (!window.RetellWebClient) {
          throw new Error('RetellWebClient is not available');
        }

        const retellWebClient = new window.RetellWebClient();
        console.log('Retell client created successfully');

        retellWebClient.on('call_started', () => {
          console.log('Call started');
          setIsConnected(true);
          setCallStatus('connected');
          setError(null);
          setIsConnecting(false);
        });

        retellWebClient.on('call_ended', () => {
          console.log('Call ended');
          setIsConnected(false);
          setCallStatus('ended');
          setIsConnecting(false);
          if (onCallEnd) {
            onCallEnd();
          }
        });

        retellWebClient.on('error', (error) => {
          console.error('Retell error:', error);
          setError(`Call error: ${error.message || JSON.stringify(error)}`);
          setIsConnecting(false);
          setIsConnected(false);
          setCallStatus('error');
        });

        retellWebClient.on('update', (update) => {
          console.log('Call update:', update);
        });

        retellWebClientRef.current = retellWebClient;
        console.log('Retell client initialized and stored in ref');

      } catch (error) {
        console.error('Error initializing Retell client:', error);
        setError(`Failed to initialize call client: ${error.message}`);
      }
    };

    loadRetellSDK();

    return () => {
      if (retellWebClientRef.current) {
        try {
          retellWebClientRef.current.stopCall();
        } catch (error) {
          console.error('Error stopping call:', error);
        }
      }

      // Clean up script if we added it
      if (scriptElement && scriptElement.parentNode) {
        scriptElement.parentNode.removeChild(scriptElement);
      }
    };
  }, [onCallEnd]);

  const startCall = async () => {
    console.log('Starting call...');

    if (!retellWebClientRef.current) {
      console.error('Call client not initialized, trying to reinitialize...');

      // Try to reinitialize if RetellWebClient is available
      if (window.RetellWebClient) {
        try {
          const retellWebClient = new window.RetellWebClient();
          retellWebClientRef.current = retellWebClient;
          console.log('Client reinitialized successfully');
        } catch (reinitError) {
          setError(`Call client not initialized and failed to reinitialize: ${reinitError.message}`);
          return;
        }
      } else {
        setError('Retell SDK not loaded. Please refresh the page and try again.');
        return;
      }
    }

    setIsConnecting(true);
    setError(null);
    setCallStatus('connecting');

    try {
      console.log('Calling startCall with:', {
        accessToken: accessToken?.substring(0, 20) + '...',
        callId: callId
      });

      await retellWebClientRef.current.startCall({
        accessToken: accessToken,
        callId: callId,
        enableUpdate: true,
      });

      console.log('StartCall completed successfully');

    } catch (error) {
      console.error('Error starting call:', error);
      setError(`Failed to start call: ${error.message || JSON.stringify(error)}`);
      setIsConnecting(false);
      setCallStatus('error');
    }
  };

  const endCall = () => {
    if (retellWebClientRef.current) {
      try {
        retellWebClientRef.current.stopCall();
        setIsConnected(false);
        setIsConnecting(false);
        setCallStatus('ended');
      } catch (error) {
        console.error('Error ending call:', error);
        setError('Failed to end call properly');
      }
    }
  };

  const copyAccessToken = () => {
    navigator.clipboard.writeText(accessToken);
    alert('Access token copied to clipboard!');
  };

  return (
    <div className="web-call-interface">
      <h3>Web Call Interface</h3>

      <div className="call-info">
        <div className="info-item">
          <strong>Call ID:</strong> {callId}
        </div>
        <div className="info-item">
          <strong>Status:</strong> <span className={`status-${callStatus}`}>{callStatus}</span>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="access-token-section">
        <label>Access Token:</label>
        <div className="token-display">
          <code className="token-code">{accessToken}</code>
          <button onClick={copyAccessToken} className="copy-token-btn">
            Copy Token
          </button>
        </div>
      </div>

      <div className="call-controls">
        {!isConnected && !isConnecting && (
          <button onClick={startCall} className="start-web-call-btn">
            Connect to Call
          </button>
        )}

        {isConnecting && (
          <button disabled className="connecting-btn">
            Connecting...
          </button>
        )}

        {isConnected && (
          <button onClick={endCall} className="end-call-btn">
            End Call
          </button>
        )}
      </div>

      <div className="call-instructions">
        <h4>How to Connect:</h4>
        <ol>
          <li>Click "Connect to Call" button above</li>
          <li>Allow microphone access when prompted</li>
          <li>Start speaking with the AI agent</li>
          <li>Click "End Call" when finished</li>
        </ol>

        <div className="alternative-access">
          <h4>Alternative Access:</h4>
          <p>You can also connect to this call using the access token above in any Retell-compatible interface.</p>
        </div>

        <div className="debug-info">
          <h4>Debug Information:</h4>
          <div className="debug-item">
            <strong>SDK Loaded:</strong> {window.RetellWebClient ? 'Yes' : 'No'}
          </div>
          <div className="debug-item">
            <strong>Client Initialized:</strong> {retellWebClientRef.current ? 'Yes' : 'No'}
          </div>
          <div className="debug-item">
            <strong>Browser:</strong> {navigator.userAgent.split(' ').slice(-2).join(' ')}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebCallInterface;