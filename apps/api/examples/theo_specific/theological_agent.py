"""
Theological Agent Pattern Implementation
Adapts pocketflow-agent for theological analysis and biblical interpretation

Cookbook Reference: pocketflow-agent/nodes.py, flow.py
Pattern Adaptations: 
- Theological reasoning with biblical hermeneutics
- Biblical reference validation and citation
- Confidence scoring for theological accuracy
"""

from pocketflow import AsyncNode, AsyncFlow
import openai
import yaml
import re


class TheologicalReasoningNode(AsyncNode):
    """
    Analyzes theological questions using biblical hermeneutics
    Cookbook Reference: pocketflow-agent/nodes.py - ReasoningNode
    Max Lines: 150 (validate with: wc -l theological_agent.py)
    """
    
    def prep(self, shared_store):
        """Validate theological query input"""
        required_keys = ["theological_question", "biblical_context"]
        for key in required_keys:
            if key not in shared_store:
                raise ValueError(f"Missing required key: {key}")
        
        return {
            "question": shared_store["theological_question"],
            "context": shared_store.get("biblical_context", ""),
            "hermeneutical_approach": shared_store.get("approach", "grammatical-historical")
        }
    
    async def exec(self, data):
        """Perform theological reasoning with LLM"""
        system_prompt = f"""You are a biblical theologian with expertise in {data['hermeneutical_approach']} hermeneutics.
        Provide theological analysis based on biblical text and sound exegetical principles.
        Include relevant biblical references and maintain doctrinal accuracy."""
        
        try:
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {data['question']}\nContext: {data['context']}"}
                ],
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            return {
                "theological_analysis": analysis,
                "biblical_references": self.extract_biblical_refs(analysis),
                "reasoning_chain": self.extract_reasoning(analysis)
            }
            
        except Exception as e:
            return {"error": f"Theological reasoning failed: {str(e)}", "recoverable": True}
    
    def post(self, result, shared_store):
        """Process theological analysis results"""
        if "error" in result:
            shared_store["reasoning_error"] = result["error"]
            return
        
        shared_store["output_theological_analysis"] = result["theological_analysis"]
        shared_store["output_biblical_references"] = result["biblical_references"]
        shared_store["temp_reasoning_chain"] = result["reasoning_chain"]
    
    def extract_biblical_refs(self, text):
        """Extract biblical references from analysis"""
        # Simple regex for biblical references (e.g., John 3:16, Romans 8:28)
        pattern = r'\b\d?\s*[A-Z][a-z]+\s+\d+:\d+(?:-\d+)?\b'
        return re.findall(pattern, text)
    
    def extract_reasoning(self, text):
        """Extract reasoning chain from theological analysis"""
        sentences = text.split('.')
        return [s.strip() for s in sentences if len(s.strip()) > 10]


class BiblicalValidationNode(AsyncNode):
    """
    Validates biblical references and theological accuracy
    Cookbook Reference: pocketflow-agent/nodes.py - ValidationNode
    Max Lines: 150
    """
    
    def prep(self, shared_store):
        """Prepare biblical validation data"""
        return {
            "references": shared_store.get("output_biblical_references", []),
            "analysis": shared_store.get("output_theological_analysis", "")
        }
    
    async def exec(self, data):
        """Validate biblical references and theological content"""
        validation_results = {
            "valid_references": [],
            "invalid_references": [],
            "theological_accuracy": 0.0,
            "validation_notes": []
        }
        
        # Validate each biblical reference
        for ref in data["references"]:
            if await self.validate_reference(ref):
                validation_results["valid_references"].append(ref)
            else:
                validation_results["invalid_references"].append(ref)
        
        # Calculate theological accuracy score
        accuracy = len(validation_results["valid_references"]) / max(len(data["references"]), 1)
        validation_results["theological_accuracy"] = min(accuracy * 0.85 + 0.15, 1.0)
        
        return validation_results
    
    def post(self, result, shared_store):
        """Store validation results"""
        shared_store["output_validation_results"] = result
        shared_store["output_accuracy_score"] = result["theological_accuracy"]
    
    async def validate_reference(self, reference):
        """Validate individual biblical reference"""
        # Simplified validation - in production would check against biblical database
        books = ["Genesis", "Exodus", "Matthew", "John", "Romans", "Ephesians"]
        return any(book in reference for book in books)


class TheologicalAnalysisFlow(AsyncFlow):
    """
    Orchestrates comprehensive theological analysis workflow
    Cookbook Reference: pocketflow-agent/flow.py
    """
    
    def __init__(self):
        self.reasoning_node = TheologicalReasoningNode()
        self.validation_node = BiblicalValidationNode()
    
    async def run(self, input_data):
        """Execute theological analysis flow"""
        shared_store = {
            "theological_question": input_data["question"],
            "biblical_context": input_data.get("context", ""),
            "hermeneutical_approach": input_data.get("approach", "grammatical-historical")
        }
        
        try:
            # Step 1: Theological reasoning
            await self.reasoning_node.run(shared_store)
            
            if "reasoning_error" in shared_store:
                return {"error": shared_store["reasoning_error"]}
            
            # Step 2: Biblical validation
            await self.validation_node.run(shared_store)
            
            # Return comprehensive theological response
            return {
                "theological_response": shared_store["output_theological_analysis"],
                "biblical_references": shared_store["output_biblical_references"],
                "accuracy_score": shared_store["output_accuracy_score"],
                "validation_results": shared_store["output_validation_results"],
                "status": "completed"
            }
            
        except Exception as e:
            return {"error": f"Theological analysis flow failed: {str(e)}", "status": "failed"}


# Example usage and testing
async def test_theological_agent():
    """Test the theological agent pattern"""
    flow = TheologicalAnalysisFlow()
    
    test_query = {
        "question": "What does the Bible teach about faith and works?",
        "context": "Exploring the relationship between faith and works in salvation",
        "approach": "grammatical-historical"
    }
    
    result = await flow.run(test_query)
    print("Theological Analysis Result:", result)
    
    # Validate line count
    import subprocess
    line_count = subprocess.run(['wc', '-l', __file__], capture_output=True, text=True)
    print(f"File line count: {line_count.stdout.strip()}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_theological_agent())