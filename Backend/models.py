from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Retell AI Webhook Models
class RetellWebhookEvent(BaseModel):
    event_type: str
    data: Dict[str, Any]

class CallStartedData(BaseModel):
    call_id: str
    agent_id: str
    call_type: str
    customer_number: Optional[str] = None

class CallAnalysisData(BaseModel):
    call_id: str
    call_analysis: Dict[str, Any]
    transcript: str
    recording_url: Optional[str] = None

# Database Models
class ConversationPrompt(BaseModel):
    id: Optional[str] = None
    name: str
    content: str
    agent_instructions: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CallRecord(BaseModel):
    id: Optional[str] = None
    call_id: str
    agent_id: str
    prompt_id: Optional[str] = None
    raw_transcript: str
    processed_summary: Optional[str] = None
    call_analysis: Optional[Dict[str, Any]] = None
    recording_url: Optional[str] = None
    access_token: Optional[str] = None
    call_type: str = "phone_call"  # phone_call, web_call
    status: str = "active"  # active, completed, failed, initiated, registered
    driver_name: Optional[str] = None
    load_number: Optional[str] = None
    phone_number: Optional[str] = None
    llm_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# API Response Models
class ProcessedTranscript(BaseModel):
    summary: str
    key_points: List[str]
    sentiment: str
    duration: Optional[str] = None
    participant_count: int

class PromptInterpretation(BaseModel):
    agent_response: str
    follow_up_questions: List[str]
    conversation_direction: str

# Call Initiation Models
class StartCallRequest(BaseModel):
    driver_name: str = Field(..., description="Name of the driver")
    phone_number: str = Field(..., description="Driver's phone number in E.164 format")
    load_number: str = Field(..., description="Load number for reference")
    agent_prompt: str = Field(..., description="Custom prompt for the agent")
    agent_logic: str = Field(..., description="Conversation logic for the agent")

class StartCallResponse(BaseModel):
    success: bool
    call_id: Optional[str] = None
    message: str
    agent_id: Optional[str] = None
    access_token: Optional[str] = None
    error: Optional[str] = None

class AgentConfigRequest(BaseModel):
    agent_name: str = Field(..., description="Name for the agent")
    prompt: str = Field(..., description="System prompt for the agent")
    logic: str = Field(..., description="Conversation logic")
    voice_id: str = Field(default="default", description="Voice ID to use")

class AgentConfigResponse(BaseModel):
    success: bool
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    message: str
    error: Optional[str] = None