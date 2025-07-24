"""
EventStreamNode for SSE message formatting

Following PocketFlow Node pattern for handling SSE message formatting.
Formats job status data into proper SSE event format.
"""

from typing import Dict, Any
from ...utils.sse_formatter import SSEFormatter


class EventStreamNode:
    """Formats job status data into SSE event format following PocketFlow patterns"""
    
    def __init__(self):
        """Initialize the event stream node"""
        self.event_counter = 0
        self.formatter = SSEFormatter()
    
    async def prep(self, shared_store: Dict[str, Any]) -> bool:
        """Validate SSE event data and format requirements"""
        try:
            if 'event_data' not in shared_store:
                shared_store['error'] = "Missing event_data for SSE formatting"
                return False
            
            event_data = shared_store['event_data']
            is_valid, error_msg = self.formatter.validate_event_data(event_data)
            
            if not is_valid:
                shared_store['error'] = error_msg
                return False
            
            return True
            
        except Exception as e:
            shared_store['error'] = f"Event stream prep failed: {str(e)}"
            return False
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format event data into SSE-compliant format"""
        try:
            event_data = data['event_data']
            self.event_counter += 1
            
            sse_event, event_metadata = self.formatter.create_sse_event(
                event_data, self.event_counter
            )
            
            return {
                'success': True,
                'sse_event': sse_event,
                'event_metadata': event_metadata,
                'formatted': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to format SSE event: {str(e)}",
                'sse_event': None
            }
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Apply final formatting and validation to SSE event"""
        try:
            if not result.get('success', False):
                error_output = self.formatter.create_error_event(
                    result.get('error', 'Unknown formatting error')
                )
                return {
                    'sse_output': error_output,
                    'formatted': False,
                    'error': result.get('error', 'Unknown formatting error')
                }
            
            include_event_id = shared_store.get('include_event_id', False)
            include_event_type = shared_store.get('include_event_type', False)
            
            sse_output = self.formatter.format_sse_lines(
                result['sse_event'],
                result['event_metadata'],
                include_event_id,
                include_event_type
            )
            
            return {
                'sse_output': sse_output,
                'sse_event': result['sse_event'],
                'formatted': True,
                'event_metadata': result.get('event_metadata')
            }
            
        except Exception as e:
            error_output = self.formatter.create_error_event(
                f'Post-formatting failed: {str(e)}'
            )
            return {
                'sse_output': error_output,
                'formatted': False,
                'error': f'Post-formatting failed: {str(e)}'
            }
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete SSE event formatting workflow"""
        if not await self.prep(shared_store):
            error_output = self.formatter.create_error_event(
                shared_store.get('error', 'Preparation failed')
            )
            return {
                'sse_output': error_output,
                'formatted': False,
                'error': shared_store.get('error', 'Preparation failed')
            }
        
        exec_result = await self.exec(shared_store)
        final_result = await self.post(exec_result, shared_store)
        
        return final_result