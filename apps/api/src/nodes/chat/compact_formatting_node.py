"""
CompactFormattingNode for conversational text formatting requests.

Streamlined replacement for formatting_node.py to comply with PocketFlow 150-line limit.
Handles common formatting commands like bullet points, summaries, tables, etc.
"""

import asyncio
import logging
import time
import aiohttp
from typing import Dict, Any, Optional
from pocketflow import AsyncNode

logger = logging.getLogger(__name__)


class CompactFormattingNode(AsyncNode):
    """Handles conversational text formatting requests with session history integration."""
    
    def __init__(self, model="gpt-4", temperature=0.3):
        super().__init__()
        self.model = model
        self.temperature = temperature
        
        self.patterns = {
            "bullet_points": ["bullet", "list format"],
            "numbered_list": ["numbered", "1. 2. 3."],
            "summary": ["summarize", "brief", "concise"],
            "table_format": ["table", "tabular", "columns"],
            "formal_tone": ["formal", "academic"],
            "paragraph_breaks": ["paragraphs", "break up"]
        }
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate request and retrieve previous response from session history."""
        try:
            if 'session_id' not in shared_store:
                return {"error": "Session expired. Please start a new conversation."}
            if 'message' not in shared_store:
                return {"error": "Invalid formatting command."}
            
            previous_response = shared_store.get('previous_response')
            if not previous_response:
                previous_response = await self._retrieve_previous_response(shared_store['session_id'])
                if not previous_response:
                    return {"error": "I don't have a previous response to format. Please ask me a question first."}
            
            command_type = self._parse_formatting_command(shared_store['message'])
            if not command_type:
                return {"error": "Try commands like 'make bullet points', 'summarize', or 'format as table'."}
            
            return {"success": True}
        except Exception as e:
            logger.error(f"CompactFormattingNode prep error: {e}")
            return {"error": "Unable to retrieve conversation history. Please try again."}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute LLM formatting request with specialized prompt."""
        try:
            previous_response = shared_store.get('previous_response')
            if not previous_response:
                previous_response = await self._retrieve_previous_response(shared_store['session_id'])
            
            message = shared_store['message']
            command_type = self._parse_formatting_command(message)
            
            if not command_type or not previous_response:
                return {"success": False, "error": "Invalid formatting request"}
            
            prompt = self._build_formatting_prompt(command_type, previous_response, message)
            from ...utils.openai_client import get_openai_client
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            formatted_content = response.choices[0].message.content.strip() or previous_response
            
            return {
                "success": True,
                "generated_answer": formatted_content,
                "original_text": previous_response,
                "command_type": command_type,
                "formatting_time": time.time()
            }
            
        except Exception as e:
            logger.error(f"Formatting execution error: {e}")
            return {
                "success": False,
                "error": "I encountered an issue while formatting. Here's the original response:",
                "generated_answer": shared_store.get('previous_response', ''),
                "original_text": shared_store.get('previous_response', '')
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store formatting results in shared store."""
        try:
            exec_result = shared_store.get('exec_result', {})
            
            if exec_result.get('success', False):
                shared_store['generated_answer'] = exec_result['generated_answer']
                shared_store['original_text'] = exec_result.get('original_text', '')
                shared_store['command_type'] = exec_result.get('command_type', '')
                
                return {"next_state": "formatted"}
            else:
                shared_store['generated_answer'] = exec_result.get('generated_answer', '')
                shared_store['formatting_error'] = exec_result.get('error', 'Unknown formatting error')
                return {"next_state": "failed"}
        except Exception as e:
            logger.error(f"CompactFormattingNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    def _parse_formatting_command(self, message: str) -> Optional[str]:
        """Parse user message to determine formatting command type."""
        message_lower = message.lower()
        for command_type, keywords in self.patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return command_type
        return None
    
    def _build_formatting_prompt(self, command_type: str, text: str, command: str) -> str:
        """Build formatting prompt based on command type."""
        formats = {
            "bullet_points": "Convert to bullet points", "numbered_list": "Convert to numbered list",
            "summary": "Summarize this text", "table_format": "Format as table",
            "formal_tone": "Rewrite formally", "paragraph_breaks": "Break into paragraphs"
        }
        action = formats.get(command_type, "Format this text")
        return f"{action}:\n{text}\nUser: {command}"
    
    async def _retrieve_previous_response(self, session_id: str) -> Optional[str]:
        """Retrieve previous response from session history via SSE endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8001/api/sse/history/{session_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        messages = data.get('messages', [])
                        for message in reversed(messages):
                            if message.get('role') == 'assistant' and message.get('content'):
                                return message['content']
            return None
        except Exception:
            return None