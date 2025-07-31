# PUBLIC_INTERFACE
"""
AI service for transcription and summarization functionality.
Contains stub implementations for AI integrations that can be replaced with actual services.
"""

import asyncio
from typing import List, Dict, Any
from decouple import config
import httpx


class AIService:
    """
    AI service for handling transcription and summarization tasks.
    
    This class provides methods for AI-powered features with stub implementations
    that can be replaced with actual AI service integrations.
    """
    
    def __init__(self):
        """Initialize AI service with configuration."""
        self.openai_api_key = config("OPENAI_API_KEY", default="")
        self.use_mock_responses = config("USE_MOCK_AI", default=True, cast=bool)
    
    async def generate_summary(self, transcript: str) -> str:
        """
        Generate AI-powered summary from transcript text.
        
        Args:
            transcript: Full video transcript text
            
        Returns:
            str: Generated summary
        """
        if self.use_mock_responses or not self.openai_api_key:
            return await self._generate_mock_summary(transcript)
        
        return await self._generate_openai_summary(transcript)
    
    async def _generate_mock_summary(self, transcript: str) -> str:
        """
        Generate a mock summary for development/testing purposes.
        
        Args:
            transcript: Full video transcript text
            
        Returns:
            str: Mock generated summary
        """
        # Simulate processing delay
        await asyncio.sleep(1)
        
        # Extract key points from transcript (simple approach)
        words = transcript.split()
        word_count = len(words)
        
        if word_count < 100:
            summary = "This is a short video covering basic concepts."
        elif word_count < 500:
            summary = "This video provides an overview of the topic with practical examples and explanations."
        else:
            summary = "This comprehensive video covers multiple aspects of the subject matter, including detailed explanations, examples, and practical applications. Key concepts are thoroughly explained with supporting information."
        
        # Add some context based on common educational keywords
        educational_keywords = ["learn", "tutorial", "course", "lesson", "teach", "explain"]
        if any(keyword in transcript.lower() for keyword in educational_keywords):
            summary += " The content is educational and suitable for learning purposes."
        
        return summary
    
    async def _generate_openai_summary(self, transcript: str) -> str:
        """
        Generate summary using OpenAI API.
        
        Args:
            transcript: Full video transcript text
            
        Returns:
            str: AI-generated summary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an AI assistant that creates concise, informative summaries of educational video content. Focus on key concepts, main points, and practical takeaways."
                            },
                            {
                                "role": "user",
                                "content": f"Please create a comprehensive summary of this video transcript:\n\n{transcript}"
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    # Fallback to mock if API fails
                    return await self._generate_mock_summary(transcript)
                    
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to mock summary
            return await self._generate_mock_summary(transcript)
    
    async def extract_key_points(self, transcript: str, max_points: int = 5) -> List[str]:
        """
        Extract key points from transcript.
        
        Args:
            transcript: Full video transcript text
            max_points: Maximum number of key points to extract
            
        Returns:
            List[str]: List of key points
        """
        if self.use_mock_responses or not self.openai_api_key:
            return await self._extract_mock_key_points(transcript, max_points)
        
        return await self._extract_openai_key_points(transcript, max_points)
    
    async def _extract_mock_key_points(self, transcript: str, max_points: int) -> List[str]:
        """
        Extract mock key points for development/testing.
        
        Args:
            transcript: Full video transcript text
            max_points: Maximum number of key points
            
        Returns:
            List[str]: Mock key points
        """
        # Simulate processing delay
        await asyncio.sleep(0.5)
        
        # Simple key point extraction based on sentence length and keywords
        sentences = transcript.split('. ')
        key_points = []
        
        important_keywords = [
            'important', 'key', 'main', 'primary', 'essential', 'crucial',
            'remember', 'note', 'concept', 'principle', 'rule', 'method'
        ]
        
        for sentence in sentences:
            if len(sentence) > 50 and any(keyword in sentence.lower() for keyword in important_keywords):
                key_points.append(sentence.strip() + '.')
                if len(key_points) >= max_points:
                    break
        
        # Fill with general points if not enough found
        while len(key_points) < min(max_points, 3):
            key_points.append(f"Key concept {len(key_points) + 1} from the video content.")
        
        return key_points[:max_points]
    
    async def _extract_openai_key_points(self, transcript: str, max_points: int) -> List[str]:
        """
        Extract key points using OpenAI API.
        
        Args:
            transcript: Full video transcript text
            max_points: Maximum number of key points
            
        Returns:
            List[str]: AI-extracted key points
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": f"Extract the {max_points} most important key points from this educational content. Return them as a simple list, one point per line."
                            },
                            {
                                "role": "user",
                                "content": transcript
                            }
                        ],
                        "max_tokens": 300,
                        "temperature": 0.5
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return [point.strip() for point in content.split('\n') if point.strip()][:max_points]
                else:
                    return await self._extract_mock_key_points(transcript, max_points)
                    
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return await self._extract_mock_key_points(transcript, max_points)
    
    async def generate_timestamped_notes(self, transcript_entries: List[Dict]) -> List[Dict[str, Any]]:
        """
        Generate timestamped notes from transcript entries.
        
        Args:
            transcript_entries: List of transcript entries with timestamps
            
        Returns:
            List[Dict]: Timestamped notes with enhanced content
        """
        timestamped_notes = []
        
        for entry in transcript_entries:
            # Skip very short entries
            if len(entry.get('text', '')) < 20:
                continue
            
            note = {
                'timestamp': int(entry.get('start', 0)),
                'text': entry.get('text', ''),
                'enhanced': False
            }
            
            # Add enhancement for important-sounding content
            if any(keyword in entry.get('text', '').lower() for keyword in 
                   ['important', 'key', 'remember', 'note', 'main']):
                note['enhanced'] = True
                note['text'] = f"📝 {note['text']}"
            
            timestamped_notes.append(note)
        
        return timestamped_notes
