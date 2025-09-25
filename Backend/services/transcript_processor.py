import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
from database import get_supabase_client
from models import CallRecord, ProcessedTranscript

class TranscriptProcessorService:
    def __init__(self):
        self.supabase = get_supabase_client()

    async def process_raw_transcript(self, raw_transcript: str, call_analysis: Dict[str, Any] = None) -> ProcessedTranscript:
        """Process raw transcript into structured summary"""

        # Clean and parse transcript
        cleaned_transcript = self._clean_transcript(raw_transcript)

        # Extract key information
        summary = self._generate_summary(cleaned_transcript)
        key_points = self._extract_key_points(cleaned_transcript)
        sentiment = self._analyze_sentiment(cleaned_transcript)
        duration = self._calculate_duration(cleaned_transcript, call_analysis)
        participant_count = self._count_participants(cleaned_transcript)

        return ProcessedTranscript(
            summary=summary,
            key_points=key_points,
            sentiment=sentiment,
            duration=duration,
            participant_count=participant_count
        )

    async def save_processed_call(self, call_record: CallRecord) -> bool:
        """Save processed call record to database"""
        try:
            # Convert to dict and handle datetime serialization
            call_data = call_record.dict(exclude_none=True)

            # Convert datetime objects to ISO format strings
            for key, value in call_data.items():
                if isinstance(value, datetime):
                    call_data[key] = value.isoformat()

            if call_record.id:
                # Update existing record
                response = self.supabase.table("call_records").update(call_data).eq("id", call_record.id).execute()
            else:
                # Insert new record
                response = self.supabase.table("call_records").insert(call_data).execute()

            return len(response.data) > 0
        except Exception as e:
            print(f"Error saving call record: {e}")
            return False

    async def get_call_by_id(self, call_id: str) -> CallRecord:
        """Retrieve call record by call_id"""
        try:
            response = self.supabase.table("call_records").select("*").eq("call_id", call_id).single().execute()
            if response.data:
                # Convert ISO format datetime strings back to datetime objects
                call_data = response.data
                datetime_fields = ['started_at', 'ended_at', 'created_at', 'updated_at']
                for field in datetime_fields:
                    if call_data.get(field):
                        try:
                            call_data[field] = datetime.fromisoformat(call_data[field].replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            # Handle cases where datetime might not be in expected format
                            pass

                return CallRecord(**call_data)
        except Exception as e:
            print(f"Error fetching call record: {e}")
        return None

    def _clean_transcript(self, raw_transcript: str) -> str:
        """Clean and normalize the raw transcript"""
        if not raw_transcript:
            return ""

        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', raw_transcript.strip())

        # Remove timestamps if present (format: [00:00:00])
        cleaned = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', cleaned)

        # Remove speaker indicators if inconsistent
        # This is a basic cleanup - adjust based on Retell AI's transcript format
        cleaned = re.sub(r'^(Speaker \d+:|Agent:|User:|Customer:)\s*', '', cleaned, flags=re.MULTILINE)

        return cleaned.strip()

    def _generate_summary(self, transcript: str) -> str:
        """Generate a concise summary of the conversation"""
        if not transcript:
            return "No transcript available"

        # Basic summarization logic
        sentences = transcript.split('. ')

        # Take first few sentences for basic summary
        if len(sentences) <= 3:
            return transcript

        # Extract key sentences (this is simplified - in production use NLP)
        summary_sentences = []

        # Add opening
        if sentences:
            summary_sentences.append(sentences[0])

        # Look for important keywords
        important_keywords = ['problem', 'issue', 'solution', 'purchase', 'order', 'help', 'question']
        for sentence in sentences[1:-1]:
            if any(keyword in sentence.lower() for keyword in important_keywords):
                summary_sentences.append(sentence)
                if len(summary_sentences) >= 3:
                    break

        # Add closing if available
        if len(sentences) > 1 and len(summary_sentences) < 3:
            summary_sentences.append(sentences[-1])

        return '. '.join(summary_sentences) + '.'

    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract key discussion points from the transcript"""
        key_points = []

        if not transcript:
            return key_points

        # Look for question indicators
        questions = re.findall(r'[^.!?]*\?', transcript)
        for question in questions[:3]:  # Limit to 3 questions
            key_points.append(f"Question: {question.strip()}")

        # Look for problem indicators
        problems = re.findall(r'[^.!?]*(?:problem|issue|trouble|error)[^.!?]*[.!?]', transcript, re.IGNORECASE)
        for problem in problems[:2]:  # Limit to 2 problems
            key_points.append(f"Issue: {problem.strip()}")

        # Look for solution indicators
        solutions = re.findall(r'[^.!?]*(?:solution|resolve|fix|help)[^.!?]*[.!?]', transcript, re.IGNORECASE)
        for solution in solutions[:2]:  # Limit to 2 solutions
            key_points.append(f"Solution: {solution.strip()}")

        return key_points[:5]  # Maximum 5 key points

    def _analyze_sentiment(self, transcript: str) -> str:
        """Analyze overall sentiment of the conversation"""
        if not transcript:
            return "neutral"

        transcript_lower = transcript.lower()

        # Count positive and negative indicators
        positive_words = ['thank', 'great', 'excellent', 'good', 'happy', 'satisfied', 'perfect', 'wonderful']
        negative_words = ['problem', 'issue', 'bad', 'terrible', 'awful', 'disappointed', 'angry', 'frustrated']

        positive_count = sum(1 for word in positive_words if word in transcript_lower)
        negative_count = sum(1 for word in negative_words if word in transcript_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _calculate_duration(self, transcript: str, call_analysis: Dict[str, Any] = None) -> str:
        """Calculate or estimate call duration"""
        if call_analysis and 'duration' in call_analysis:
            duration_seconds = call_analysis['duration']
            return str(timedelta(seconds=duration_seconds))

        # Estimate based on transcript length (rough approximation)
        word_count = len(transcript.split())
        estimated_minutes = max(1, word_count // 150)  # Average speaking rate ~150 words/minute

        return f"{estimated_minutes}:00"

    def _count_participants(self, transcript: str) -> int:
        """Count number of unique participants in the conversation"""
        # Look for speaker indicators
        speaker_patterns = [
            r'Speaker \d+:',
            r'Agent:',
            r'User:',
            r'Customer:',
            r'Representative:'
        ]

        unique_speakers = set()
        for pattern in speaker_patterns:
            matches = re.findall(pattern, transcript)
            unique_speakers.update(matches)

        # Default to 2 if no clear indicators (agent + customer)
        return max(2, len(unique_speakers))