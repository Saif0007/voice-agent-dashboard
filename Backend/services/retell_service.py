import httpx
import json
from typing import Dict, Any, Optional
from config import RETELL_API_KEY, RETELL_FROM_NUMBER


class RetellService:
    def __init__(self):
        if not RETELL_API_KEY:
            raise ValueError("RETELL_API_KEY is not configured")

        self.api_key = RETELL_API_KEY
        self.base_url = "https://api.retellai.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        print(f"RetellService initialized with API key length: {len(self.api_key)}")

    async def create_web_call(
        self,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a web call using Retell AI

        Args:
            agent_id: Retell AI agent ID
            metadata: Optional metadata to pass with the call

        Returns:
            Dict containing call details including call_id and access_token
        """
        print(f"Creating web call with agent {agent_id}")

        async with httpx.AsyncClient() as client:
            payload = {
                "agent_id": agent_id,
                "metadata": metadata or {}
            }

            print(f"Payload: {payload}")
            print(f"Headers: {self.headers}")

            try:
                response = await client.post(
                    f"{self.base_url}/v2/create-web-call",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text}")

                if response.status_code not in [200, 201]:
                    error_detail = response.text
                    raise Exception(f"Failed to create web call: {response.status_code} - {error_detail}")

                return response.json()

            except httpx.TimeoutException:
                raise Exception("Request to Retell AI timed out")
            except httpx.RequestError as e:
                raise Exception(f"Network error connecting to Retell AI: {e}")
            except Exception as e:
                raise Exception(f"Error creating web call: {e}")

    async def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """
        Get call details from Retell AI

        Args:
            call_id: The call ID

        Returns:
            Dict containing call details
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/get-call/{call_id}",
                headers=self.headers
            )

            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Failed to get call details: {response.status_code} - {error_detail}")

            return response.json()

    async def create_agent(
        self,
        agent_name: str,
        voice_id: str,
        prompt: str,
        webhook_url: Optional[str] = None,
        llm_id: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Create a new agent in Retell AI

        Args:
            agent_name: Name for the agent
            voice_id: Voice ID to use
            prompt: System prompt for the agent
            webhook_url: Optional webhook URL for callbacks

        Returns:
            Dict containing agent details including agent_id
        """
        print(f"Creating agent: {agent_name}")

        # First, try to create a simple LLM with the prompt
        llm_response = await self.create_retell_llm(prompt)
        actual_llm_id = llm_response.get("llm_id", llm_id)

        async with httpx.AsyncClient() as client:
            payload = {
                "agent_name": agent_name,
                "voice_id": voice_id,
                "language": "en-US",
                "response_engine": {
                    "type": "retell-llm",
                    "llm_id": actual_llm_id
                }
            }

            # Add webhook URL if provided
            if webhook_url:
                payload["webhook_url"] = webhook_url

            print(f"Agent payload: {json.dumps(payload, indent=2)}")

            try:
                response = await client.post(
                    f"{self.base_url}/create-agent",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

                print(f"Agent creation response status: {response.status_code}")
                print(f"Agent creation response text: {response.text}")

                if response.status_code not in [200, 201]:
                    error_detail = response.text
                    raise Exception(f"Failed to create agent: {response.status_code} - {error_detail}")

                return response.json()

            except httpx.TimeoutException:
                raise Exception("Request to Retell AI timed out while creating agent")
            except httpx.RequestError as e:
                raise Exception(f"Network error connecting to Retell AI while creating agent: {e}")
            except Exception as e:
                raise Exception(f"Error creating agent: {e}")

    async def list_agents(self) -> Dict[str, Any]:
        """List all agents"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/list-agents",
                headers=self.headers
            )

            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Failed to list agents: {response.status_code} - {error_detail}")

            return response.json()

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get specific agent details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/get-agent/{agent_id}",
                headers=self.headers
            )

            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Failed to get agent: {response.status_code} - {error_detail}")

            return response.json()

    async def update_agent(
        self,
        agent_id: str,
        agent_name: Optional[str] = None,
        prompt: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing agent"""
        async with httpx.AsyncClient() as client:
            # First get current agent details
            current_agent = await self.get_agent(agent_id)

            # Prepare update payload with only changed fields
            payload = {
                "agent_name": agent_name or current_agent.get("agent_name"),
                "voice_id": voice_id or current_agent.get("voice_id"),
                "language": current_agent.get("language", "en-US"),
                "response_engine": current_agent.get("response_engine"),
                "general_prompt": prompt or current_agent.get("general_prompt"),
                "begin_message": (prompt[:200] if prompt else current_agent.get("begin_message")),
                "general_tools": current_agent.get("general_tools", []),
                "states": current_agent.get("states", [])
            }

            response = await client.patch(
                f"{self.base_url}/update-agent/{agent_id}",
                headers=self.headers,
                json=payload
            )

            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Failed to update agent: {response.status_code} - {error_detail}")

            return response.json()

    async def create_retell_llm(self, prompt: str) -> Dict[str, Any]:
        """Create a Retell LLM with the given prompt"""
        async with httpx.AsyncClient() as client:
            payload = {
                "general_prompt": prompt,
                "model": "gpt-4o-mini",
                "general_tools": []
            }

            print(f"Creating LLM with payload: {json.dumps(payload, indent=2)}")

            try:
                response = await client.post(
                    f"{self.base_url}/create-retell-llm",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

                print(f"LLM creation response status: {response.status_code}")
                print(f"LLM creation response text: {response.text}")

                if response.status_code != 201:  # 201 is typical for creation
                    error_detail = response.text
                    raise Exception(f"Failed to create LLM: {response.status_code} - {error_detail}")

                return response.json()

            except httpx.TimeoutException:
                raise Exception("Request to Retell AI timed out while creating LLM")
            except httpx.RequestError as e:
                raise Exception(f"Network error connecting to Retell AI while creating LLM: {e}")
            except Exception as e:
                raise Exception(f"Error creating LLM: {e}")