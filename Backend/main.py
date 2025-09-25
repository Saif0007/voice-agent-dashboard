from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import hmac
import hashlib
import json

from models import (
    RetellWebhookEvent, CallStartedData, CallAnalysisData, CallRecord, ProcessedTranscript,
    StartCallRequest, StartCallResponse, AgentConfigRequest, AgentConfigResponse
)
from services.prompt_interpreter import PromptInterpreterService
from services.transcript_processor import TranscriptProcessorService
from services.retell_service import RetellService
from config import RETELL_WEBHOOK_SECRET

app = FastAPI(title="Retell AI Webhook Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
prompt_service = PromptInterpreterService()
transcript_service = TranscriptProcessorService()
retell_service = RetellService()


def verify_webhook_signature(request: Request, payload: bytes) -> bool:
    """Verify Retell AI webhook signature"""
    if not RETELL_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured

    signature = request.headers.get("x-retell-signature")
    if not signature:
        return False

    expected_signature = hmac.new(
        RETELL_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


@app.get("/")
async def root():
    return {"message": "Retell AI Webhook Backend", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/test/retell-config")
async def test_retell_config():
    """Test endpoint to verify Retell AI configuration"""
    try:
        from config import RETELL_API_KEY, RETELL_WEBHOOK_SECRET

        return {
            "retell_api_key_configured": bool(RETELL_API_KEY),
            "retell_webhook_secret_configured": bool(RETELL_WEBHOOK_SECRET),
            "retell_service_initialized": bool(retell_service),
            "api_key_length": len(RETELL_API_KEY) if RETELL_API_KEY else 0
        }
    except Exception as e:
        return {"error": str(e), "configured": False}


@app.get("/api/test/retell-connection")
async def test_retell_connection():
    """Test endpoint to verify connection to Retell AI"""
    try:
        # Try to list agents to test the connection
        agents = await retell_service.list_agents()
        return {
            "success": True,
            "message": "Successfully connected to Retell AI",
            "agents_count": len(agents.get("results", [])) if agents else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to connect to Retell AI"
        }


@app.post("/webhook/retell")
async def retell_webhook(request: Request):
    """Handle Retell AI webhook events"""
    try:
        # Get raw payload for signature verification
        payload = await request.body()

        # Verify webhook signature
        if not verify_webhook_signature(request, payload):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse webhook event
        event_data = json.loads(payload.decode())
        event = RetellWebhookEvent(**event_data)

        # Route based on event type
        if event.event_type == "call_started":
            return await handle_call_started(event)
        elif event.event_type == "call_ended":
            return await handle_call_ended(event)
        elif event.event_type == "call_analyzed":
            return await handle_call_analyzed(event)
        else:
            # Log unknown event type
            print(f"Unknown event type: {event.event_type}")
            return {"status": "ignored", "event_type": event.event_type}

    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_call_started(event: RetellWebhookEvent):
    """Handle call started event"""
    try:
        call_data = CallStartedData(**event.data)

        # Get active prompt for the agent
        prompt = await prompt_service.get_active_prompt_for_agent(call_data.agent_id)

        # Create initial call record
        call_record = CallRecord(
            call_id=call_data.call_id,
            agent_id=call_data.agent_id,
            prompt_id=prompt.id if prompt else None,
            raw_transcript="",
            status="active",
            started_at=datetime.utcnow()
        )

        # Save call record
        await transcript_service.save_processed_call(call_record)

        # Return initial agent configuration based on prompt
        response = {
            "status": "call_started",
            "call_id": call_data.call_id,
            "agent_config": {
                "initial_message": prompt.content[:200] if prompt else "Hello! How can I help you today?",
                "prompt_id": prompt.id if prompt else None
            }
        }

        return response

    except Exception as e:
        print(f"Error handling call_started: {e}")
        return {"status": "error", "message": str(e)}


async def handle_call_ended(event: RetellWebhookEvent):
    """Handle call ended event"""
    try:
        call_id = event.data.get("call_id")

        # Update call record status
        call_record = await transcript_service.get_call_by_id(call_id)
        if call_record:
            call_record.status = "completed"
            call_record.ended_at = datetime.utcnow()
            await transcript_service.save_processed_call(call_record)

        return {"status": "call_ended", "call_id": call_id}

    except Exception as e:
        print(f"Error handling call_ended: {e}")
        return {"status": "error", "message": str(e)}


async def handle_call_analyzed(event: RetellWebhookEvent):
    """Handle call analysis event with transcript processing"""
    try:
        analysis_data = CallAnalysisData(**event.data)

        # Get existing call record
        call_record = await transcript_service.get_call_by_id(analysis_data.call_id)
        if not call_record:
            # Create new record if it doesn't exist
            call_record = CallRecord(
                call_id=analysis_data.call_id,
                agent_id=event.data.get("agent_id", "unknown"),
                raw_transcript=analysis_data.transcript,
                status="completed"
            )
        else:
            # Update existing record
            call_record.raw_transcript = analysis_data.transcript

        # Process transcript
        processed_transcript = await transcript_service.process_raw_transcript(
            analysis_data.transcript,
            analysis_data.call_analysis
        )

        # Update call record with processed data
        call_record.processed_summary = processed_transcript.summary
        call_record.call_analysis = analysis_data.call_analysis
        call_record.recording_url = analysis_data.recording_url
        call_record.status = "completed"
        call_record.ended_at = datetime.utcnow()

        # Save updated record
        await transcript_service.save_processed_call(call_record)

        return {
            "status": "call_analyzed",
            "call_id": analysis_data.call_id,
            "processed_summary": processed_transcript.dict()
        }

    except Exception as e:
        print(f"Error handling call_analyzed: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/calls/{call_id}")
async def get_call_details(call_id: str):
    """Get detailed call information"""
    try:
        call_record = await transcript_service.get_call_by_id(call_id)

        # If not found in database, try to get it directly from Retell AI
        if not call_record:
            try:
                print(f"Call {call_id} not found in database, fetching from Retell AI...")
                retell_call_details = await retell_service.get_call_details(call_id)

                # Create a basic call record structure from Retell data
                return {
                    "call_id": call_id,
                    "agent_id": retell_call_details.get("agent_id"),
                    "status": retell_call_details.get("call_status", "unknown"),
                    "raw_transcript": retell_call_details.get("transcript", ""),
                    "call_analysis": retell_call_details.get("call_analysis"),
                    "recording_url": retell_call_details.get("recording_url"),
                    "started_at": retell_call_details.get("start_timestamp"),
                    "ended_at": retell_call_details.get("end_timestamp"),
                    "source": "retell_api",
                    "retell_data": retell_call_details
                }

            except Exception as retell_error:
                print(f"Call not found in database or Retell AI: {retell_error}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Call {call_id} not found in database or Retell AI system"
                )

        return call_record.dict()

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching call details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/calls/{call_id}/transcript")
async def get_processed_transcript(call_id: str):
    """Get processed transcript for a call"""
    try:
        call_record = await transcript_service.get_call_by_id(call_id)
        if not call_record:
            raise HTTPException(status_code=404, detail="Call not found")

        if not call_record.raw_transcript:
            raise HTTPException(status_code=404, detail="Transcript not available")

        # Reprocess transcript to get latest format
        processed = await transcript_service.process_raw_transcript(
            call_record.raw_transcript,
            call_record.call_analysis
        )

        return processed.dict()

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing transcript: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/agent/create", response_model=AgentConfigResponse)
async def create_agent(request: AgentConfigRequest):
    """Create a new Retell AI agent with custom prompt and logic"""
    try:
        # Combine prompt and logic for the agent
        combined_prompt = f"{request.prompt}\n\nConversation Logic:\n{request.logic}"

        # Create agent in Retell AI
        agent_response = await retell_service.create_agent(
            agent_name=request.agent_name,
            voice_id=request.voice_id,
            prompt=combined_prompt
        )

        return AgentConfigResponse(
            success=True,
            agent_id=agent_response.get("agent_id"),
            agent_name=agent_response.get("agent_name"),
            message="Agent created successfully"
        )

    except Exception as e:
        print(f"Error creating agent: {e}")
        return AgentConfigResponse(
            success=False,
            message="Failed to create agent",
            error=str(e)
        )


@app.post("/api/call/start", response_model=StartCallResponse)
async def start_test_call(request: StartCallRequest):
    """Start a test call with Retell AI"""
    try:
        # Create a temporary agent for this call
        agent_name = f"Driver Call Agent - {request.load_number}"
        combined_prompt = f"""You are a professional logistics coordinator calling about load #{request.load_number}.

Driver Information:
- Driver Name: {request.driver_name}
- Load Number: {request.load_number}

{request.agent_prompt}

Conversation Logic:
{request.agent_logic}

Keep the conversation professional and focused on the load details. Gather all necessary information efficiently."""

        # Create agent
        agent_response = await retell_service.create_agent(
            agent_name=agent_name,
            voice_id="11labs-Adrian",
            prompt=combined_prompt
        )

        agent_id = agent_response.get("agent_id")

        # Start the web call
        call_response = await retell_service.create_web_call(
            agent_id=agent_id,
            metadata={
                "driver_name": request.driver_name,
                "load_number": request.load_number,
                "phone_number": request.phone_number,
                "call_type": "test_web_call"
            }
        )

        call_id = call_response.get("call_id")

        # Store call record in database
        call_record = CallRecord(
            call_id=call_id,
            agent_id=agent_id,
            raw_transcript="",
            status="registered",  # Use the status from Retell AI response
            access_token=call_response.get("access_token"),
            call_type="web_call",
            driver_name=request.driver_name,
            load_number=request.load_number,
            phone_number=request.phone_number,
            llm_id=call_response.get("llm_id"),
            started_at=datetime.utcnow()
        )

        await transcript_service.save_processed_call(call_record)

        return StartCallResponse(
            success=True,
            call_id=call_id,
            agent_id=agent_id,
            message=f"Web call initiated successfully for {request.driver_name} (load {request.load_number})",
            access_token=call_response.get("access_token")
        )

    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        print(f"Error starting test call: {error_message}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

        return StartCallResponse(
            success=False,
            message="Failed to start test call",
            error=error_message
        )


@app.get("/api/call/{call_id}/status")
async def get_call_status(call_id: str):
    """Get current status of a call"""
    try:
        # Get call from database first
        call_record = await transcript_service.get_call_by_id(call_id)

        # If not found in database, try to get it directly from Retell AI
        if not call_record:
            try:
                print(f"Call {call_id} not found in database, checking Retell AI...")
                retell_call_details = await retell_service.get_call_details(call_id)

                return {
                    "call_id": call_id,
                    "status": retell_call_details.get("call_status", "unknown"),
                    "agent_id": retell_call_details.get("agent_id"),
                    "started_at": retell_call_details.get("start_timestamp"),
                    "ended_at": retell_call_details.get("end_timestamp"),
                    "has_transcript": bool(retell_call_details.get("transcript")),
                    "has_analysis": bool(retell_call_details.get("call_analysis")),
                    "source": "retell_api",
                    "retell_data": retell_call_details
                }

            except Exception as retell_error:
                print(f"Call not found in database or Retell AI: {retell_error}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Call {call_id} not found in database or Retell AI system"
                )

        # Get latest status from Retell AI if call exists in database
        try:
            retell_call_details = await retell_service.get_call_details(call_id)
            retell_status = retell_call_details.get("call_status", call_record.status)

            # Update local record if status changed
            if retell_status != call_record.status and retell_status in ["completed", "ended"]:
                call_record.status = retell_status
                if retell_call_details.get("end_timestamp"):
                    call_record.ended_at = retell_call_details.get("end_timestamp")
                await transcript_service.save_processed_call(call_record)

        except Exception as retell_error:
            print(f"Could not get latest status from Retell AI: {retell_error}")
            retell_status = call_record.status

        return {
            "call_id": call_id,
            "status": retell_status,
            "agent_id": call_record.agent_id,
            "started_at": call_record.started_at,
            "ended_at": call_record.ended_at,
            "has_transcript": bool(call_record.raw_transcript),
            "has_analysis": bool(call_record.call_analysis),
            "source": "database"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/agents")
async def list_agents():
    """List all available agents"""
    try:
        agents = await retell_service.list_agents()
        return agents

    except Exception as e:
        print(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/agent/{agent_id}")
async def get_agent_details(agent_id: str):
    """Get details of a specific agent"""
    try:
        agent = await retell_service.get_agent(agent_id)
        return agent

    except Exception as e:
        print(f"Error getting agent details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/call/{call_id}/sync")
async def sync_call_from_retell(call_id: str):
    """Sync a call from Retell AI to local database"""
    try:
        print(f"Syncing call {call_id} from Retell AI to database...")

        # Get call details from Retell AI
        retell_call_details = await retell_service.get_call_details(call_id)

        # Create call record for database
        call_record = CallRecord(
            call_id=call_id,
            agent_id=retell_call_details.get("agent_id", "unknown"),
            raw_transcript=retell_call_details.get("transcript", ""),
            call_analysis=retell_call_details.get("call_analysis"),
            recording_url=retell_call_details.get("recording_url"),
            access_token=retell_call_details.get("access_token"),
            call_type=retell_call_details.get("call_type", "web_call"),
            status=retell_call_details.get("call_status", "completed"),
            llm_id=retell_call_details.get("llm_id"),
            started_at=retell_call_details.get("start_timestamp"),
            ended_at=retell_call_details.get("end_timestamp")
        )

        # Save to database
        success = await transcript_service.save_processed_call(call_record)

        if success:
            return {
                "success": True,
                "message": f"Call {call_id} synced successfully to database",
                "call_data": call_record.dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save call to database")

    except Exception as e:
        print(f"Error syncing call: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync call {call_id}: {str(e)}"
        )