from typing import Optional, List
from database import get_supabase_client
from models import ConversationPrompt, PromptInterpretation

class PromptInterpreterService:
    def __init__(self):
        self.supabase = get_supabase_client()

    async def get_prompt_by_id(self, prompt_id: str) -> Optional[ConversationPrompt]:
        """Retrieve a conversation prompt from the database"""
        try:
            response = self.supabase.table("conversation_prompts").select("*").eq("id", prompt_id).single().execute()
            if response.data:
                return ConversationPrompt(**response.data)
        except Exception as e:
            print(f"Error fetching prompt: {e}")
        return None

    async def get_active_prompt_for_agent(self, agent_id: str) -> Optional[ConversationPrompt]:
        """Get the active prompt for a specific agent"""
        try:
            response = self.supabase.table("agent_prompts").select("""
                conversation_prompts(*)
            """).eq("agent_id", agent_id).eq("is_active", True).single().execute()

            if response.data and response.data.get("conversation_prompts"):
                return ConversationPrompt(**response.data["conversation_prompts"])
        except Exception as e:
            print(f"Error fetching agent prompt: {e}")
        return None

    async def interpret_conversation_context(self, prompt: ConversationPrompt, conversation_history: str, user_input: str) -> PromptInterpretation:
        """Interpret the current conversation context based on the prompt"""

        # Extract key elements from the prompt
        agent_instructions = prompt.agent_instructions
        prompt_content = prompt.content

        # Analyze conversation flow
        agent_response = self._generate_agent_response(
            agent_instructions,
            prompt_content,
            conversation_history,
            user_input
        )

        follow_up_questions = self._generate_follow_up_questions(
            prompt_content,
            conversation_history,
            user_input
        )

        conversation_direction = self._determine_conversation_direction(
            prompt_content,
            conversation_history
        )

        return PromptInterpretation(
            agent_response=agent_response,
            follow_up_questions=follow_up_questions,
            conversation_direction=conversation_direction
        )

    def _generate_agent_response(self, instructions: str, prompt: str, history: str, user_input: str) -> str:
        """Generate contextual agent response based on prompt and conversation"""

        # Basic response generation logic
        # In production, this would integrate with an LLM service

        if "greeting" in user_input.lower() or not history:
            return f"Hello! {prompt[:100]}..."

        # Check for specific keywords in the prompt to guide response
        if "support" in instructions.lower():
            return "I understand you need assistance. How can I help you today?"
        elif "sales" in instructions.lower():
            return "I'd be happy to discuss our products and services with you."
        else:
            return "Thank you for sharing that. Let me help you with your inquiry."

    def _generate_follow_up_questions(self, prompt: str, history: str, user_input: str) -> List[str]:
        """Generate relevant follow-up questions"""

        questions = []

        # Basic question generation based on conversation state
        if not history:
            questions.extend([
                "What brings you here today?",
                "How can I assist you?",
                "Is there something specific you'd like to know about?"
            ])
        else:
            questions.extend([
                "Can you tell me more about that?",
                "What would you like to know next?",
                "Is there anything else I can help clarify?"
            ])

        return questions[:3]  # Limit to 3 questions

    def _determine_conversation_direction(self, prompt: str, history: str) -> str:
        """Determine the overall direction of the conversation"""

        if not history:
            return "introduction"

        # Basic sentiment and direction analysis
        if "problem" in history.lower() or "issue" in history.lower():
            return "problem_solving"
        elif "buy" in history.lower() or "purchase" in history.lower():
            return "sales"
        elif "thank" in history.lower():
            return "conclusion"
        else:
            return "information_gathering"