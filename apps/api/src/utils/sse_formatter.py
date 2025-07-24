"""
SSE formatting utilities for EventStreamNode.
Extracted to maintain PocketFlow 150-line limit.
"""
import json
from typing import Dict, Any, List
from datetime import datetime, timezone


class SSEFormatter:
    """Utility class for SSE event formatting and validation."""
    
    @staticmethod
    def validate_event_data(event_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate event data structure and types."""
        required_fields = ['status', 'progress', 'step']
        for field in required_fields:
            if field not in event_data:
                return False, f"Missing required field '{field}' in event data"
        
        if not isinstance(event_data['progress'], (int, float)):
            return False, "Progress must be a number"
        
        if not isinstance(event_data['status'], str):
            return False, "Status must be a string"
        
        if not isinstance(event_data['step'], str):
            return False, "Step must be a string"
        
        if not (0.0 <= event_data['progress'] <= 1.0):
            return False, "Progress must be between 0.0 and 1.0"
        
        return True, ""
    
    @staticmethod
    def create_sse_event(event_data: Dict[str, Any], event_counter: int) -> Dict[str, Any]:
        """Create SSE event structure from event data."""
        sse_event = {
            'status': event_data['status'],
            'progress': round(float(event_data['progress']), 3),
            'step': event_data['step'],
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        if 'message' in event_data and event_data['message']:
            sse_event['message'] = event_data['message']
        
        event_metadata = {
            'event_id': f"event_{event_counter}",
            'event_type': 'job_status_update'
        }
        
        return sse_event, event_metadata
    
    @staticmethod
    def format_sse_lines(sse_event: Dict[str, Any], event_metadata: Dict[str, Any], 
                        include_event_id: bool = False, include_event_type: bool = False) -> str:
        """Format SSE event into proper SSE output lines."""
        sse_lines = []
        
        if include_event_id:
            sse_lines.append(f"id: {event_metadata['event_id']}")
        
        if include_event_type:
            sse_lines.append(f"event: {event_metadata['event_type']}")
        
        sse_lines.append(f"data: {json.dumps(sse_event)}")
        sse_lines.append("")
        
        return "\n".join(sse_lines) + "\n"
    
    @staticmethod
    def create_error_event(error_message: str) -> str:
        """Create error SSE event."""
        error_data = {
            'status': 'error', 
            'progress': 0.0, 
            'step': 'format_error', 
            'message': error_message
        }
        return f"data: {json.dumps(error_data)}\n\n"