# PocketFlow Integration Architecture

## Node Architecture Patterns

**Standard Node Structure**:
```python
from pocketflow import Node, AsyncNode

class TheologicalAnalysisNode(AsyncNode):
    """
    Analyzes theological content using biblical hermeneutics
    Max 150 lines including imports and docstrings
    """
    
    async def prep(self, shared_store):
        """Validate inputs and prepare execution"""
        required_keys = ["theological_query", "context"]
        self.validate_shared_store(shared_store, required_keys)
        return shared_store["theological_query"]
    
    async def exec(self, data):
        """Core theological analysis logic"""
        # Implementation limited to ~100 lines
        analysis = await self.perform_analysis(data)
        return analysis
    
    async def post(self, result, shared_store):
        """Update shared store with results"""
        shared_store["theological_analysis"] = result
        shared_store["analysis_confidence"] = result.get("confidence", 0.0)
```

**AsyncNode for I/O Operations**:
```python
class DatabaseQueryNode(AsyncNode):
    """All database operations use AsyncNode pattern"""
    
    async def exec(self, data):
        # Database connections
        async with self.db.get_connection() as conn:
            result = await conn.fetch(data["query"])
        return result
```

## Flow Orchestration Architecture

**Sequential Flow Pattern**:
```python
class TheologicalWorkflow(AsyncFlow):
    """Orchestrates theological analysis workflow"""
    
    def __init__(self):
        self.validation_node = InputValidationNode()
        self.analysis_node = TheologicalAnalysisNode()
        self.citation_node = CitationGenerationNode()
    
    async def run(self, input_data):
        shared_store = {"input": input_data}
        
        # Sequential execution
        await self.validation_node.run(shared_store)
        await self.analysis_node.run(shared_store)
        await self.citation_node.run(shared_store)
        
        return shared_store["final_result"]
```

**Parallel Flow Pattern** (for complex workflows):
```python
class DocumentProcessingFlow(AsyncFlow):
    """Parallel processing for document analysis"""
    
    async def run(self, document_data):
        # Parallel Node execution
        tasks = [
            self.content_analysis_node.run(shared_store),
            self.reference_extraction_node.run(shared_store),
            self.theme_identification_node.run(shared_store)
        ]
        
        await asyncio.gather(*tasks)
        return self.combine_results(shared_store)
```
