"""
Hermeneutic Workflow Pattern Implementation
Adapts pocketflow-structured-output for systematic biblical interpretation

Cookbook Reference: pocketflow-structured-output/main.py, utils.py
Pattern Adaptations:
- Multi-step hermeneutical analysis (grammatical, historical, theological)
- Structured YAML output for systematic interpretation results
- Integration of biblical languages and cultural context
"""

from pocketflow import AsyncNode, AsyncFlow
import yaml
import openai
from typing import Dict, Any


class GrammaticalAnalysisNode(AsyncNode):
    """
    Performs grammatical analysis of biblical text
    Cookbook Reference: pocketflow-structured-output/utils.py - structured output patterns
    Max Lines: 150 (validate with: wc -l hermeneutic_workflow.py)
    """
    
    def prep(self, shared_store):
        """Prepare biblical text for grammatical analysis"""
        if "biblical_passage" not in shared_store:
            raise ValueError("Missing biblical_passage in shared store")
        
        return {
            "passage": shared_store["biblical_passage"],
            "original_language": shared_store.get("original_language", "detect"),
            "translation": shared_store.get("translation", "ESV")
        }
    
    async def exec(self, data):
        """Analyze grammatical structure of biblical text"""
        try:
            system_prompt = """You are a biblical scholar specializing in grammatical analysis.
            Analyze the grammatical structure, syntax, and linguistic features of biblical texts.
            Provide structured output in YAML format."""
            
            user_prompt = f"""
            Analyze the grammatical structure of this biblical passage:
            
            Passage: {data['passage']}
            Translation: {data['translation']}
            
            Provide analysis in this YAML structure:
            grammatical_analysis:
              verb_forms:
                - verb: ""
                  tense: ""
                  mood: ""
                  voice: ""
              key_nouns:
                - noun: ""
                  case: ""
                  significance: ""
              sentence_structure: ""
              grammatical_insights: []
              original_language_notes: ""
            """
            
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            # Parse YAML response
            yaml_content = self.extract_yaml(response.choices[0].message.content)
            grammatical_data = yaml.safe_load(yaml_content)
            
            return {
                "grammatical_analysis": grammatical_data["grammatical_analysis"],
                "analysis_confidence": 0.85,
                "linguistic_notes": grammatical_data["grammatical_analysis"].get("original_language_notes", "")
            }
            
        except Exception as e:
            return {"error": f"Grammatical analysis failed: {str(e)}", "recoverable": True}
    
    def post(self, result, shared_store):
        """Store grammatical analysis results"""
        if "error" in result:
            shared_store["grammatical_error"] = result["error"]
            return
        
        shared_store["output_grammatical_analysis"] = result["grammatical_analysis"]
        shared_store["temp_linguistic_notes"] = result["linguistic_notes"]
    
    def extract_yaml(self, text: str) -> str:
        """Extract YAML content from response"""
        lines = text.split('\n')
        yaml_lines = []
        in_yaml = False
        
        for line in lines:
            if line.strip().startswith('grammatical_analysis:'):
                in_yaml = True
            if in_yaml:
                yaml_lines.append(line)
        
        return '\n'.join(yaml_lines) if yaml_lines else "grammatical_analysis: {}"


class HistoricalContextNode(AsyncNode):
    """
    Analyzes historical and cultural context of biblical passages
    Cookbook Reference: pocketflow-structured-output - structured analysis patterns
    Max Lines: 150
    """
    
    def prep(self, shared_store):
        """Prepare for historical context analysis"""
        return {
            "passage": shared_store["biblical_passage"],
            "book": shared_store.get("biblical_book", ""),
            "chapter": shared_store.get("biblical_chapter", ""),
            "verse": shared_store.get("biblical_verse", "")
        }
    
    async def exec(self, data):
        """Analyze historical and cultural context"""
        try:
            system_prompt = """You are a biblical historian and archaeologist.
            Provide historical and cultural context for biblical passages.
            Focus on first-century background, customs, and cultural practices."""
            
            user_prompt = f"""
            Provide historical context analysis for:
            {data['book']} {data['chapter']}:{data['verse']}
            Passage: {data['passage']}
            
            Structure your response as YAML:
            historical_context:
              time_period: ""
              cultural_background: ""
              geographical_setting: ""
              social_customs: []
              political_climate: ""
              religious_practices: []
              archaeological_insights: []
              contextual_significance: ""
            """
            
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            
            yaml_content = self.extract_yaml(response.choices[0].message.content)
            historical_data = yaml.safe_load(yaml_content)
            
            return {
                "historical_context": historical_data["historical_context"],
                "context_confidence": 0.80,
                "archaeological_support": len(historical_data["historical_context"].get("archaeological_insights", []))
            }
            
        except Exception as e:
            return {"error": f"Historical analysis failed: {str(e)}", "recoverable": True}
    
    def post(self, result, shared_store):
        """Store historical context results"""
        if "error" in result:
            shared_store["historical_error"] = result["error"]
            return
        
        shared_store["output_historical_context"] = result["historical_context"]
        shared_store["temp_archaeological_support"] = result["archaeological_support"]
    
    def extract_yaml(self, text: str) -> str:
        """Extract YAML from historical analysis response"""
        lines = text.split('\n')
        yaml_lines = []
        in_yaml = False
        
        for line in lines:
            if line.strip().startswith('historical_context:'):
                in_yaml = True
            if in_yaml:
                yaml_lines.append(line)
        
        return '\n'.join(yaml_lines) if yaml_lines else "historical_context: {}"


class TheologicalInterpretationNode(AsyncNode):
    """
    Synthesizes theological interpretation from grammatical and historical analysis
    Cookbook Reference: pocketflow-structured-output - final synthesis patterns
    Max Lines: 150
    """
    
    def prep(self, shared_store):
        """Prepare theological interpretation data"""
        return {
            "passage": shared_store["biblical_passage"],
            "grammatical": shared_store.get("output_grammatical_analysis", {}),
            "historical": shared_store.get("output_historical_context", {}),
            "hermeneutical_approach": shared_store.get("approach", "grammatical-historical")
        }
    
    async def exec(self, data):
        """Generate comprehensive theological interpretation"""
        try:
            system_prompt = f"""You are a systematic theologian using {data['hermeneutical_approach']} hermeneutics.
            Synthesize grammatical and historical analysis into theological interpretation.
            Provide structured YAML output with clear theological conclusions."""
            
            context_summary = f"""
            Grammatical Analysis: {data['grammatical']}
            Historical Context: {data['historical']}
            """
            
            user_prompt = f"""
            Passage: {data['passage']}
            
            Based on the grammatical and historical analysis provided:
            {context_summary}
            
            Provide theological interpretation in YAML format:
            theological_interpretation:
              central_message: ""
              doctrinal_themes: []
              practical_applications: []
              cross_references: []
              theological_significance: ""
              interpretive_principles: []
              potential_controversies: []
              pastoral_implications: ""
              confidence_level: 0.0
            """
            
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            yaml_content = self.extract_yaml(response.choices[0].message.content)
            theological_data = yaml.safe_load(yaml_content)
            
            return {
                "theological_interpretation": theological_data["theological_interpretation"],
                "synthesis_complete": True,
                "interpretation_confidence": theological_data["theological_interpretation"].get("confidence_level", 0.75)
            }
            
        except Exception as e:
            return {"error": f"Theological interpretation failed: {str(e)}", "recoverable": True}
    
    def post(self, result, shared_store):
        """Store final theological interpretation"""
        if "error" in result:
            shared_store["theological_error"] = result["error"]
            return
        
        shared_store["output_theological_interpretation"] = result["theological_interpretation"]
        shared_store["output_interpretation_confidence"] = result["interpretation_confidence"]
    
    def extract_yaml(self, text: str) -> str:
        """Extract YAML from theological interpretation"""
        lines = text.split('\n')
        yaml_lines = []
        in_yaml = False
        
        for line in lines:
            if line.strip().startswith('theological_interpretation:'):
                in_yaml = True
            if in_yaml:
                yaml_lines.append(line)
        
        return '\n'.join(yaml_lines) if yaml_lines else "theological_interpretation: {}"


class HermeneuticWorkflow(AsyncFlow):
    """
    Orchestrates complete hermeneutical analysis workflow
    Cookbook Reference: pocketflow-structured-output/main.py - workflow orchestration
    """
    
    def __init__(self):
        self.grammatical_node = GrammaticalAnalysisNode()
        self.historical_node = HistoricalContextNode()
        self.theological_node = TheologicalInterpretationNode()
    
    async def run(self, input_data):
        """Execute complete hermeneutical workflow"""
        shared_store = {
            "biblical_passage": input_data["passage"],
            "biblical_book": input_data.get("book", ""),
            "biblical_chapter": input_data.get("chapter", ""),
            "biblical_verse": input_data.get("verse", ""),
            "original_language": input_data.get("language", "detect"),
            "translation": input_data.get("translation", "ESV"),
            "approach": input_data.get("hermeneutical_approach", "grammatical-historical")
        }
        
        try:
            # Step 1: Grammatical analysis
            await self.grammatical_node.run(shared_store)
            if "grammatical_error" in shared_store:
                return {"error": shared_store["grammatical_error"]}
            
            # Step 2: Historical context analysis
            await self.historical_node.run(shared_store)
            if "historical_error" in shared_store:
                return {"error": shared_store["historical_error"]}
            
            # Step 3: Theological interpretation synthesis
            await self.theological_node.run(shared_store)
            if "theological_error" in shared_store:
                return {"error": shared_store["theological_error"]}
            
            # Compile comprehensive hermeneutical analysis
            hermeneutical_result = {
                "passage_analyzed": shared_store["biblical_passage"],
                "grammatical_analysis": shared_store["output_grammatical_analysis"],
                "historical_context": shared_store["output_historical_context"],
                "theological_interpretation": shared_store["output_theological_interpretation"],
                "overall_confidence": shared_store["output_interpretation_confidence"],
                "hermeneutical_method": shared_store["approach"],
                "status": "completed"
            }
            
            return hermeneutical_result
            
        except Exception as e:
            return {"error": f"Hermeneutic workflow failed: {str(e)}", "status": "failed"}


# Example usage and testing
async def test_hermeneutic_workflow():
    """Test the hermeneutic workflow pattern"""
    workflow = HermeneuticWorkflow()
    
    test_passage = {
        "passage": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
        "book": "John",
        "chapter": "3", 
        "verse": "16",
        "translation": "ESV",
        "hermeneutical_approach": "grammatical-historical"
    }
    
    result = await workflow.run(test_passage)
    
    # Output structured YAML result
    if "error" not in result:
        print("=== HERMENEUTICAL ANALYSIS RESULT ===")
        print(yaml.dump(result, default_flow_style=False, indent=2))
    else:
        print("Error:", result["error"])


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hermeneutic_workflow())