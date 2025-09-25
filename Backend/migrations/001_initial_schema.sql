-- Supabase Database Schema for Retell AI Backend

-- Table for storing conversation prompts
CREATE TABLE IF NOT EXISTS conversation_prompts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    agent_instructions TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for mapping agents to their active prompts
CREATE TABLE IF NOT EXISTS agent_prompts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    prompt_id UUID REFERENCES conversation_prompts(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id, is_active) -- Only one active prompt per agent
);

-- Table for storing call records and transcripts
CREATE TABLE IF NOT EXISTS call_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    prompt_id UUID REFERENCES conversation_prompts(id) ON DELETE SET NULL,
    raw_transcript TEXT,
    processed_summary TEXT,
    call_analysis JSONB,
    recording_url TEXT,
    access_token TEXT,  -- For web calls
    call_type VARCHAR(50) DEFAULT 'phone_call',  -- phone_call, web_call
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, failed, initiated, registered
    driver_name VARCHAR(255),  -- Store driver name for context
    load_number VARCHAR(255),  -- Store load number for context
    phone_number VARCHAR(50),  -- Store phone number for reference
    llm_id VARCHAR(255),  -- Store the LLM ID used
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for tracking created agents and LLMs
CREATE TABLE IF NOT EXISTS retell_agents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    llm_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    voice_id VARCHAR(255) NOT NULL,
    general_prompt TEXT,
    conversation_logic TEXT,
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for tracking created LLMs
CREATE TABLE IF NOT EXISTS retell_llms (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    llm_id VARCHAR(255) UNIQUE NOT NULL,
    model VARCHAR(100) DEFAULT 'gpt-4o-mini',
    general_prompt TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_call_records_call_id ON call_records(call_id);
CREATE INDEX IF NOT EXISTS idx_call_records_agent_id ON call_records(agent_id);
CREATE INDEX IF NOT EXISTS idx_call_records_status ON call_records(status);
CREATE INDEX IF NOT EXISTS idx_call_records_call_type ON call_records(call_type);
CREATE INDEX IF NOT EXISTS idx_call_records_load_number ON call_records(load_number);
CREATE INDEX IF NOT EXISTS idx_call_records_driver_name ON call_records(driver_name);
CREATE INDEX IF NOT EXISTS idx_call_records_created_at ON call_records(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_prompts_agent_id ON agent_prompts(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_prompts_active ON agent_prompts(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_retell_agents_agent_id ON retell_agents(agent_id);
CREATE INDEX IF NOT EXISTS idx_retell_agents_llm_id ON retell_agents(llm_id);
CREATE INDEX IF NOT EXISTS idx_retell_llms_llm_id ON retell_llms(llm_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to automatically update updated_at
CREATE TRIGGER update_conversation_prompts_updated_at
    BEFORE UPDATE ON conversation_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_prompts_updated_at
    BEFORE UPDATE ON agent_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_records_updated_at
    BEFORE UPDATE ON call_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_retell_agents_updated_at
    BEFORE UPDATE ON retell_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_retell_llms_updated_at
    BEFORE UPDATE ON retell_llms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO conversation_prompts (name, content, agent_instructions) VALUES
(
    'Logistics Coordinator',
    'Hello! This is ABC Trucking Co. calling about your load assignment. How are you doing today?',
    'You are a professional logistics coordinator for ABC Trucking Co. Help drivers with load coordination, route planning, and delivery updates. Always maintain a helpful, clear, and professional tone. Prioritize safety and regulatory compliance in all interactions. Gather necessary information efficiently and provide clear next steps.'
),
(
    'Driver Check-in Agent',
    'Hi there! I''m calling to check on your current load status and see if you need any assistance with your delivery.',
    'You are a driver support specialist. Focus on understanding the driver''s current situation, any challenges they''re facing, and provide helpful solutions. Ask about ETA, any delays, special delivery instructions, and preferred communication methods. Maintain a supportive and professional tone.'
),
(
    'Load Assignment Agent',
    'Good morning! I have a new load assignment that might be perfect for you. Do you have a moment to discuss the details?',
    'You are a load assignment coordinator. Present load opportunities clearly, including pickup/delivery locations, timeframes, and compensation. Verify driver availability, gather any special requirements, and confirm acceptance. Be professional but personable in your approach.'
);

-- Sample agent-prompt mapping
INSERT INTO agent_prompts (agent_id, prompt_id, is_active)
SELECT 'agent_logistics_001', id, TRUE FROM conversation_prompts WHERE name = 'Logistics Coordinator' LIMIT 1;

-- Add some views for easier data access
CREATE OR REPLACE VIEW call_records_with_details AS
SELECT
    cr.*,
    cp.name as prompt_name,
    cp.content as prompt_content,
    ra.agent_name,
    ra.voice_id,
    rl.model as llm_model
FROM call_records cr
LEFT JOIN conversation_prompts cp ON cr.prompt_id = cp.id
LEFT JOIN retell_agents ra ON cr.agent_id = ra.agent_id
LEFT JOIN retell_llms rl ON cr.llm_id = rl.llm_id
ORDER BY cr.created_at DESC;

-- View for active agents and their prompts
CREATE OR REPLACE VIEW active_agents_with_prompts AS
SELECT
    ra.agent_id,
    ra.agent_name,
    ra.voice_id,
    cp.name as prompt_name,
    cp.content as prompt_content,
    cp.agent_instructions,
    ra.created_at as agent_created_at
FROM retell_agents ra
JOIN agent_prompts ap ON ra.agent_id = ap.agent_id
JOIN conversation_prompts cp ON ap.prompt_id = cp.id
WHERE ra.status = 'active' AND ap.is_active = TRUE;