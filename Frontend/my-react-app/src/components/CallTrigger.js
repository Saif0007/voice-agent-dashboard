import React, { useState } from 'react';

const CallTrigger = ({ agentConfig, setCallResults }) => {
  const [driverInfo, setDriverInfo] = useState({
    name: '',
    phone: '',
    loadNumber: ''
  });
  const [isCallInProgress, setIsCallInProgress] = useState(false);
  const [currentCallId, setCurrentCallId] = useState(null);
  const [isFetchingResults, setIsFetchingResults] = useState(false);
  const [manualCallId, setManualCallId] = useState('');
  const [isSyncing, setIsSyncing] = useState(false);
  const [showManualLookup, setShowManualLookup] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;

    // Format phone number for Pakistani numbers
    if (name === 'phone') {
      const formattedPhone = formatPhoneNumber(value);
      setDriverInfo(prev => ({
        ...prev,
        [name]: formattedPhone
      }));
    } else {
      setDriverInfo(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const formatPhoneNumber = (phone) => {
    // Remove all non-digit characters
    const digitsOnly = phone.replace(/\D/g, '');

    // Handle Pakistani numbers
    if (digitsOnly.startsWith('92')) {
      // Already has country code
      return `+${digitsOnly}`;
    } else if (digitsOnly.startsWith('03') && digitsOnly.length === 11) {
      // Pakistani mobile number starting with 03, convert to +92
      return `+92${digitsOnly.substring(1)}`;
    } else if (digitsOnly.length === 10 && digitsOnly.startsWith('3')) {
      // Pakistani mobile without leading 0
      return `+92${digitsOnly}`;
    }

    // Return as-is with + prefix if not empty
    return digitsOnly ? `+${digitsOnly}` : '';
  };

  const startTestCall = async () => {
    if (!driverInfo.name || !driverInfo.phone || !driverInfo.loadNumber) {
      alert('Please fill in all driver information fields');
      return;
    }

    if (!agentConfig.prompt || !agentConfig.logic) {
      alert('Please configure the agent first');
      return;
    }

    setIsCallInProgress(true);
    setCallResults(null);
    setCurrentCallId(null);

    try {
      // Make actual API call to backend
      const response = await fetch('http://localhost:8000/api/call/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          driver_name: driverInfo.name,
          phone_number: driverInfo.phone,
          load_number: driverInfo.loadNumber,
          agent_prompt: agentConfig.prompt,
          agent_logic: agentConfig.logic
        })
      });

      const result = await response.json();

      if (result.success) {
        setCurrentCallId(result.call_id);

        // Show initial success message with access token
        const message = `Web call initiated successfully!\n\nCall ID: ${result.call_id}\nAccess Token: ${result.access_token}\n\nYou can use this access token to connect to the web call.`;
        alert(message);

        // For web calls, we can immediately set some basic results since they don't auto-start
        const basicResults = {
          callId: result.call_id,
          status: 'web_call_ready',
          duration: 'N/A',
          timestamp: new Date().toISOString(),
          keyInformation: {
            'Call Type': 'Web Call',
            'Call Status': 'Ready to Connect',
            'Driver Name': driverInfo.name,
            'Load Number': driverInfo.loadNumber,
            'Access Token': result.access_token,
            'Agent ID': result.agent_id
          },
          transcript: [{
            speaker: 'System',
            message: 'Web call created successfully. Use the access token to connect to the call interface.'
          }],
          access_token: result.access_token
        };
        setCallResults(basicResults);

        // Still poll for any updates, but less frequently for web calls
        setTimeout(() => pollForCallCompletion(result.call_id), 5000);
      } else {
        throw new Error(result.error || 'Failed to start call');
      }
    } catch (error) {
      console.error('Call failed:', error);
      alert(`Call failed: ${error.message}`);
    } finally {
      setIsCallInProgress(false);
    }
  };

  const pollForCallCompletion = async (callId) => {
    const maxAttempts = 60; // Poll for up to 5 minutes (60 * 5 seconds)
    let attempts = 0;

    const pollInterval = setInterval(async () => {
      attempts++;

      try {
        // Check call status
        const statusResponse = await fetch(`http://localhost:8000/api/call/${callId}/status`);
        const statusData = await statusResponse.json();

        if (statusData.status === 'completed' || statusData.status === 'ended') {
          clearInterval(pollInterval);

          // Get full call details including transcript
          await fetchCallResults(callId);

        } else if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          alert('Call is taking longer than expected. Please check the call status manually.');

          // Still try to fetch any available results
          await fetchCallResults(callId);
        }
      } catch (error) {
        console.error('Error polling call status:', error);

        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          alert('Unable to get call status. Please try again later.');
        }
      }
    }, 5000); // Poll every 5 seconds
  };

  const fetchCallResults = async (callId) => {
    try {
      // Get call details
      const callResponse = await fetch(`http://localhost:8000/api/calls/${callId}`);
      const callData = await callResponse.json();

      // Try to get processed transcript
      let processedTranscript = null;
      try {
        const transcriptResponse = await fetch(`http://localhost:8000/api/calls/${callId}/transcript`);
        if (transcriptResponse.ok) {
          processedTranscript = await transcriptResponse.json();
        }
      } catch (transcriptError) {
        console.log('Transcript not yet available:', transcriptError);
      }

      // Format results for display
      const formattedResults = {
        callId: callId,
        status: callData.status || 'completed',
        duration: calculateDuration(callData.started_at, callData.ended_at),
        timestamp: callData.ended_at || callData.started_at,
        keyInformation: extractKeyInformation(callData.call_analysis, processedTranscript),
        transcript: formatTranscript(callData.raw_transcript),
        rawCallData: callData,
        processedTranscript: processedTranscript
      };

      setCallResults(formattedResults);

    } catch (error) {
      console.error('Error fetching call results:', error);

      // Show basic results even if detailed fetch fails
      setCallResults({
        callId: callId,
        status: 'completed',
        duration: 'Unknown',
        timestamp: new Date().toISOString(),
        keyInformation: {
          'Call Status': 'Completed',
          'Error': 'Unable to fetch detailed results'
        },
        transcript: [{ speaker: 'System', message: 'Transcript not available' }]
      });
    }
  };

  const calculateDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return 'Unknown';

    const start = new Date(startTime);
    const end = new Date(endTime);
    const durationMs = end - start;
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);

    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const extractKeyInformation = (callAnalysis, processedTranscript) => {
    const keyInfo = {};

    if (processedTranscript) {
      keyInfo['Call Summary'] = processedTranscript.summary || 'No summary available';
      keyInfo['Sentiment'] = processedTranscript.sentiment || 'Unknown';
      keyInfo['Key Points'] = processedTranscript.key_points?.join(', ') || 'None';
    }

    if (callAnalysis) {
      // Extract relevant fields from call analysis
      Object.keys(callAnalysis).forEach(key => {
        if (typeof callAnalysis[key] === 'string' || typeof callAnalysis[key] === 'number') {
          keyInfo[key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())] = callAnalysis[key];
        }
      });
    }

    // Add driver info
    keyInfo['Driver Name'] = driverInfo.name;
    keyInfo['Load Number'] = driverInfo.loadNumber;
    keyInfo['Phone Number'] = driverInfo.phone;

    return Object.keys(keyInfo).length > 0 ? keyInfo : {
      'Driver Name': driverInfo.name,
      'Load Number': driverInfo.loadNumber,
      'Call Status': 'Completed'
    };
  };

  const formatTranscript = (rawTranscript) => {
    if (!rawTranscript) {
      return [{ speaker: 'System', message: 'Transcript not available yet. It may take a few minutes to process.' }];
    }

    try {
      // Try to parse if it's JSON
      if (rawTranscript.startsWith('[') || rawTranscript.startsWith('{')) {
        const parsed = JSON.parse(rawTranscript);
        if (Array.isArray(parsed)) {
          return parsed;
        }
      }

      // If it's plain text, try to parse it
      const lines = rawTranscript.split('\n');
      const transcript = [];

      lines.forEach(line => {
        line = line.trim();
        if (line) {
          // Try to detect speaker patterns
          const speakerMatch = line.match(/^(Agent|Driver|Assistant|User|Human):\s*(.+)/i);
          if (speakerMatch) {
            transcript.push({
              speaker: speakerMatch[1],
              message: speakerMatch[2]
            });
          } else {
            // If no clear speaker pattern, treat as system message
            transcript.push({
              speaker: 'System',
              message: line
            });
          }
        }
      });

      return transcript.length > 0 ? transcript : [
        { speaker: 'System', message: rawTranscript }
      ];

    } catch (error) {
      console.error('Error formatting transcript:', error);
      return [{ speaker: 'System', message: rawTranscript || 'Transcript processing error' }];
    }
  };

  const manualFetchResults = async () => {
    const callIdToFetch = manualCallId.trim() || currentCallId;

    if (!callIdToFetch) {
      alert('Please enter a call ID or start a new call first.');
      return;
    }

    setIsFetchingResults(true);

    try {
      // First check call status
      const statusResponse = await fetch(`http://localhost:8000/api/call/${callIdToFetch}/status`);
      const statusData = await statusResponse.json();

      if (statusData.status === 'completed' || statusData.status === 'ended') {
        // Call has ended, fetch results
        await fetchCallResults(callIdToFetch);
        alert('Call results fetched successfully!');

        // If using manual call ID, update the current call ID for future operations
        if (manualCallId.trim()) {
          setCurrentCallId(callIdToFetch);
        }
      } else {
        // Call is still active
        alert(`Call is still active (Status: ${statusData.status}). Please wait for the call to complete before fetching results.`);
      }
    } catch (error) {
      console.error('Error fetching call status:', error);
      alert(`Failed to check call status for ${callIdToFetch}. Please verify the call ID is correct.`);
    } finally {
      setIsFetchingResults(false);
    }
  };

  const syncCallFromRetell = async () => {
    const callIdToSync = manualCallId.trim();

    if (!callIdToSync) {
      alert('Please enter a call ID to sync from Retell AI.');
      return;
    }

    setIsSyncing(true);

    try {
      const response = await fetch(`http://localhost:8000/api/call/${callIdToSync}/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (response.ok && result.success) {
        alert(`Call ${callIdToSync} synced successfully from Retell AI to database!`);
        setCurrentCallId(callIdToSync);
        // Automatically fetch results after successful sync
        await manualFetchResults();
      } else {
        alert(`Failed to sync call: ${result.detail || result.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error syncing call:', error);
      alert(`Failed to sync call: ${error.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="call-trigger">
      <h2>Call Management</h2>

      <div className="driver-info-form">
        <h3>Driver Information</h3>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="driver-name">Driver Name:</label>
            <input
              type="text"
              id="driver-name"
              name="name"
              value={driverInfo.name}
              onChange={handleInputChange}
              placeholder="Enter driver's name"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="driver-phone">Phone Number:</label>
            <input
              type="tel"
              id="driver-phone"
              name="phone"
              value={driverInfo.phone}
              onChange={handleInputChange}
              placeholder="03001234567 (will format to +923001234567)"
              className="form-input"
            />
          </div>
        </div>
        <div className="form-group load-number-group">
          <label htmlFor="load-number">Load Number:</label>
          <input
            type="text"
            id="load-number"
            name="loadNumber"
            value={driverInfo.loadNumber}
            onChange={handleInputChange}
            placeholder="Enter load number"
            className="form-input"
          />
        </div>
      </div>

      <div className="call-actions">
        <button
          onClick={startTestCall}
          disabled={isCallInProgress}
          className="start-call-btn"
        >
          {isCallInProgress ? (currentCallId ? 'Waiting for Call to Complete...' : 'Initiating Call...') : 'Start Test Call'}
        </button>
      </div>

      <div className="manual-call-section">
        <div className="manual-call-header">
          <h3>Manual Call ID Lookup</h3>
          <button
            onClick={() => setShowManualLookup(!showManualLookup)}
            className="toggle-manual-btn"
          >
            {showManualLookup ? 'Hide' : 'Show'}
          </button>
        </div>

        {showManualLookup && (
          <div className="manual-call-content">
            <div className="form-group">
              <label htmlFor="manual-call-id">Call ID:</label>
              <input
                type="text"
                id="manual-call-id"
                value={manualCallId}
                onChange={(e) => setManualCallId(e.target.value)}
                placeholder="Enter call ID to check status (e.g., call_d4f2985c03281ec70ff9b2f8e37)"
                className="form-input"
              />
              <small className="input-help">
                Enter any call ID to check its status and fetch results. Use "Sync from Retell AI" if the call isn't in your database yet.
              </small>
            </div>

            <div className="manual-call-actions">
              <button
                onClick={manualFetchResults}
                disabled={isFetchingResults}
                className="fetch-results-btn"
              >
                {isFetchingResults ? 'Checking Call Status...' : 'Fetch Call Results'}
              </button>
              <button
                onClick={syncCallFromRetell}
                disabled={isSyncing || !manualCallId.trim()}
                className="sync-call-btn"
              >
                {isSyncing ? 'Syncing from Retell AI...' : 'Sync from Retell AI'}
              </button>
            </div>

            <div className="call-status-info">
              {(manualCallId.trim() || currentCallId) && (
                <div className="call-status">
                  <small>
                    Will fetch: {manualCallId.trim() || currentCallId}
                    {manualCallId.trim() && currentCallId && manualCallId.trim() !== currentCallId && (
                      <span className="call-source"> (manual override)</span>
                    )}
                    {!manualCallId.trim() && currentCallId && (
                      <span className="call-source"> (current call)</span>
                    )}
                  </small>
                </div>
              )}
              {!manualCallId.trim() && !currentCallId && (
                <div className="call-status">
                  <small className="no-call-id">Enter a call ID above or start a new call</small>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CallTrigger;