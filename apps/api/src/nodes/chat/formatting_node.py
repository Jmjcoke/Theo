"""FormattingNode for conversational text formatting requests."""

import asyncio
import logging
import time
import aiohttp
from typing import Dict, Any, Optional
from pocketflow import AsyncNode

logger = logging.getLogger(__name__)

PATTERNS = {
    "bullet_points": ["bullet", "list format"], "numbered_list": ["numbered", "1. 2. 3."],
    "summary": ["summarize", "brief", "concise"], "table_format": ["table", "tabular", "columns"],
    "formal_tone": ["formal", "academic"], "paragraph_breaks": ["paragraphs", "break up"]
}

PROMPTS = {
    "bullet_points": "Convert to bullet points:\n{text}\nUser: {command}",
    "numbered_list": "Convert to numbered list:\n{text}\nUser: {command}", 
    "summary": "Summarize this text:\n{text}\nUser: {command}",
    "table_format": "Format as table:\n{text}\nUser: {command}",
    "formal_tone": "Rewrite formally:\n{text}\nUser: {command}",
    "paragraph_breaks": "Break into paragraphs:\n{text}\nUser: {command}"
}

ERRORS = {
    "no_previous": "I don't have a previous response to format. Please ask me a question first.",
    "invalid_command": "Try commands like 'make bullet points', 'summarize', or 'format as table'.",
    "llm_failure": "I encountered an issue while formatting. Here's the original response:",
    "session_not_found": "Session expired. Please start a new conversation.",
    "api_failure": "Unable to retrieve conversation history. Please try again."
}

class FormattingNode(AsyncNode):
    """Handles conversational text formatting requests with session history integration."""
    
    def __init__(self, model="gpt-4", temperature=0.3):
        super().__init__()
        self.model = model
        self.temperature = temperature
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate request and retrieve previous response from session history."""
        try:
            if 'session_id' not in shared_store:
                return {"error": ERRORS["session_not_found"]}
            if 'message' not in shared_store:
                return {"error": ERRORS["invalid_command"]}
            
            previous_response = shared_store.get('previous_response')
            if not previous_response:
                previous_response = await self._retrieve_previous_response(shared_store['session_id'])
                if not previous_response:
                    return {"error": ERRORS["no_previous"]}
            
            command_type = self._parse_formatting_command(shared_store['message'])
            if not command_type:
                return {"error": ERRORS["invalid_command"]}
            
            return {
                "formatting_command_type": command_type,
                "previous_response": previous_response,
                "message": shared_store['message'],
                "formatting_start_time": time.time()
            }
        except Exception as e:
            logger.error(f"FormattingNode prep error: {e}")
            return {"error": ERRORS["api_failure"]}
    
    async def exec_async(self, prep_result: dict) -> dict:
        """Execute LLM formatting request with specialized prompt."""
        try:
            if "error" in prep_result:
                return {"success": False, "error": prep_result["error"]}
            
            command_type = prep_result.get('formatting_command_type')
            previous_text = prep_result.get('previous_response')
            user_command = prep_result.get('message')
            
            if not command_type or not previous_text or not user_command:
                return {"success": False, "error": ERRORS["invalid_command"]}
            
            prompt = PROMPTS[command_type].format(text=previous_text, command=user_command)
            from ...utils.openai_client import get_openai_client
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            formatted_content = response.choices[0].message.content.strip() or previous_text
            
            return {
                "success": True,
                "generated_answer": formatted_content,
                "original_text": previous_text,
                "formatting_applied": command_type,
                "confidence": 0.9,
                "generation_model": self.model
            }
        except Exception as e:
            logger.error(f"FormattingNode exec error: {e}")
            return {
                "success": False,
                "error": ERRORS["llm_failure"],
                "generated_answer": prep_result.get('previous_response', '') if isinstance(prep_result, dict) else ''
            }
    
    async def post_async(self, shared_store: Dict[str, Any], prep_result: dict, exec_result: dict) -> dict:
        """Process formatting results and update metadata."""
        try:
            start_time = prep_result.get('formatting_start_time', 0)
            shared_store['processing_time_ms'] = int((time.time() - start_time) * 1000) if start_time else 0
            
            if exec_result.get('success', False):
                shared_store.update({
                    'generated_answer': exec_result['generated_answer'],
                    'original_text': exec_result['original_text'],
                    'formatting_applied': exec_result['formatting_applied'],
                    'confidence': exec_result['confidence'],
                    'generation_model': exec_result['generation_model']
                })
                return {"next_state": "success"}
            else:
                shared_store['formatting_error'] = exec_result.get('error', 'Unknown formatting error')
                shared_store['generated_answer'] = exec_result.get('generated_answer', '')
                return {"next_state": "error"}
        except Exception as e:
            logger.error(f"FormattingNode post error: {e}")
            return {"next_state": "error"}
    
    async def _retrieve_previous_response(self, session_id: str) -> Optional[str]:
        """Retrieve last AI response from chat history API."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"http://localhost:8001/api/chat/history/{session_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        messages = data.get('messages', [])
                        for message in reversed(messages):
                            if message.get('role') == 'assistant' and message.get('content', '').strip():
                                return message['content'].strip()
                    else:
                        logger.warning(f"Chat history API returned {response.status} for session {session_id}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout retrieving chat history for session: {session_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve chat history: {e}")
            return None
    
    def _parse_formatting_command(self, command: str) -> Optional[str]:
        """Parse user command to identify formatting type."""
        command_lower = command.lower()
        for cmd_type, patterns in PATTERNS.items():
            for pattern in patterns:
                if pattern in command_lower:
                    return cmd_type
        return None