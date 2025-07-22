"""
Biblical RAG (Retrieval-Augmented Generation) Pattern Implementation
Adapts pocketflow-rag for biblical text search and theological document retrieval

Cookbook Reference: pocketflow-rag/nodes.py, flow.py
Pattern Adaptations:
- Biblical text vector search and semantic retrieval
- Theological document knowledge base integration  
- Citation and source attribution for biblical references
"""

from pocketflow import AsyncNode, AsyncFlow
import faiss
import numpy as np
import openai
from typing import List, Dict


class BiblicalRetrievalNode(AsyncNode):
    """
    Retrieves relevant biblical passages and theological documents
    Cookbook Reference: pocketflow-rag/nodes.py - RAGRetrievalNode
    Max Lines: 150 (validate with: wc -l biblical_rag.py)
    """
    
    def prep(self, shared_store):
        """Validate query and prepare retrieval parameters"""
        if "theological_query" not in shared_store:
            raise ValueError("Missing theological_query in shared store")
        
        return {
            "query": shared_store["theological_query"],
            "max_biblical_passages": shared_store.get("max_biblical_results", 5),
            "max_documents": shared_store.get("max_doc_results", 3),
            "similarity_threshold": shared_store.get("threshold", 0.7)
        }
    
    async def exec(self, data):
        """Perform semantic search across biblical and theological content"""
        try:
            # Generate query embedding
            query_embedding = await self.get_embedding(data["query"])
            
            # Search biblical passages
            biblical_results = await self.search_biblical_passages(
                query_embedding, 
                data["max_biblical_passages"],
                data["similarity_threshold"]
            )
            
            # Search theological documents
            doc_results = await self.search_theological_docs(
                query_embedding,
                data["max_documents"], 
                data["similarity_threshold"]
            )
            
            return {
                "biblical_passages": biblical_results,
                "theological_documents": doc_results,
                "query_embedding": query_embedding.tolist(),
                "retrieval_metadata": {
                    "biblical_count": len(biblical_results),
                    "document_count": len(doc_results)
                }
            }
            
        except Exception as e:
            return {"error": f"Biblical retrieval failed: {str(e)}", "recoverable": True}
    
    def post(self, result, shared_store):
        """Store retrieval results in shared store"""
        if "error" in result:
            shared_store["retrieval_error"] = result["error"]
            return
        
        shared_store["retrieved_biblical_passages"] = result["biblical_passages"]
        shared_store["retrieved_theological_docs"] = result["theological_documents"]
        shared_store["temp_query_embedding"] = result["query_embedding"]
        shared_store["temp_retrieval_metadata"] = result["retrieval_metadata"]
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for query text"""
        response = await openai.AsyncOpenAI().embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return np.array(response.data[0].embedding)
    
    async def search_biblical_passages(self, query_embedding: np.ndarray, limit: int, threshold: float) -> List[Dict]:
        """Search biblical passage vector database"""
        # Simplified mock implementation - in production would use real vector DB
        mock_biblical_passages = [
            {"reference": "John 3:16", "text": "For God so loved the world...", "score": 0.85},
            {"reference": "Romans 8:28", "text": "And we know that in all things...", "score": 0.78},
            {"reference": "Ephesians 2:8-9", "text": "For it is by grace you have been saved...", "score": 0.82}
        ]
        
        # Filter by threshold and limit
        filtered_results = [p for p in mock_biblical_passages if p["score"] >= threshold]
        return filtered_results[:limit]
    
    async def search_theological_docs(self, query_embedding: np.ndarray, limit: int, threshold: float) -> List[Dict]:
        """Search theological document vector database"""
        # Simplified mock implementation
        mock_theological_docs = [
            {"title": "Systematic Theology - Salvation", "excerpt": "The doctrine of salvation...", "score": 0.79},
            {"title": "Biblical Hermeneutics", "excerpt": "Principles of biblical interpretation...", "score": 0.73}
        ]
        
        filtered_results = [d for d in mock_theological_docs if d["score"] >= threshold]
        return filtered_results[:limit]


class BiblicalGenerationNode(AsyncNode):
    """
    Generates theological responses using retrieved biblical content
    Cookbook Reference: pocketflow-rag/nodes.py - RAGGenerationNode
    Max Lines: 150
    """
    
    def prep(self, shared_store):
        """Prepare generation data from retrieved content"""
        return {
            "query": shared_store["theological_query"],
            "biblical_passages": shared_store.get("retrieved_biblical_passages", []),
            "theological_docs": shared_store.get("retrieved_theological_docs", []),
            "generation_style": shared_store.get("style", "scholarly")
        }
    
    async def exec(self, data):
        """Generate theological response using retrieved content"""
        try:
            # Prepare context from retrieved content
            biblical_context = self.format_biblical_context(data["biblical_passages"])
            doc_context = self.format_document_context(data["theological_docs"])
            
            system_prompt = f"""You are a biblical scholar generating responses based on retrieved content.
            Use the provided biblical passages and theological documents to inform your response.
            Maintain {data['generation_style']} tone and always cite sources."""
            
            user_prompt = f"""
            Query: {data['query']}
            
            Biblical Context:
            {biblical_context}
            
            Theological Context:
            {doc_context}
            
            Please provide a comprehensive theological response with proper citations.
            """
            
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            generated_response = response.choices[0].message.content
            
            return {
                "theological_response": generated_response,
                "citations": self.extract_citations(generated_response),
                "source_passages": data["biblical_passages"],
                "source_documents": data["theological_docs"]
            }
            
        except Exception as e:
            return {"error": f"Biblical generation failed: {str(e)}", "recoverable": True}
    
    def post(self, result, shared_store):
        """Store generated response"""
        if "error" in result:
            shared_store["generation_error"] = result["error"]
            return
        
        shared_store["output_theological_response"] = result["theological_response"]
        shared_store["output_citations"] = result["citations"]
        shared_store["output_source_attribution"] = {
            "biblical_passages": result["source_passages"],
            "theological_documents": result["source_documents"]
        }
    
    def format_biblical_context(self, passages: List[Dict]) -> str:
        """Format biblical passages for context"""
        context_parts = []
        for passage in passages:
            context_parts.append(f"{passage['reference']}: {passage['text']}")
        return "\n".join(context_parts)
    
    def format_document_context(self, documents: List[Dict]) -> str:
        """Format theological documents for context"""
        context_parts = []
        for doc in documents:
            context_parts.append(f"{doc['title']}: {doc['excerpt']}")
        return "\n".join(context_parts)
    
    def extract_citations(self, text: str) -> List[str]:
        """Extract citations from generated text"""
        import re
        # Extract biblical references and document titles
        citations = re.findall(r'(?:\w+\s+\d+:\d+|\w+\s+Theology)', text)
        return list(set(citations))


class BiblicalRAGFlow(AsyncFlow):
    """
    Orchestrates biblical RAG workflow for theological knowledge retrieval
    Cookbook Reference: pocketflow-rag/flow.py
    """
    
    def __init__(self):
        self.retrieval_node = BiblicalRetrievalNode()
        self.generation_node = BiblicalGenerationNode()
    
    async def run(self, input_data):
        """Execute biblical RAG flow"""
        shared_store = {
            "theological_query": input_data["query"],
            "max_biblical_results": input_data.get("max_biblical", 5),
            "max_doc_results": input_data.get("max_docs", 3),
            "threshold": input_data.get("similarity_threshold", 0.7),
            "style": input_data.get("generation_style", "scholarly")
        }
        
        try:
            # Step 1: Retrieve biblical and theological content
            await self.retrieval_node.run(shared_store)
            
            if "retrieval_error" in shared_store:
                return {"error": shared_store["retrieval_error"]}
            
            # Step 2: Generate theological response with retrieved content
            await self.generation_node.run(shared_store)
            
            if "generation_error" in shared_store:
                return {"error": shared_store["generation_error"]}
            
            return {
                "theological_response": shared_store["output_theological_response"],
                "citations": shared_store["output_citations"],
                "source_attribution": shared_store["output_source_attribution"],
                "retrieval_metadata": shared_store["temp_retrieval_metadata"],
                "status": "completed"
            }
            
        except Exception as e:
            return {"error": f"Biblical RAG flow failed: {str(e)}", "status": "failed"}


# Example usage and testing
async def test_biblical_rag():
    """Test the biblical RAG pattern"""
    flow = BiblicalRAGFlow()
    
    test_query = {
        "query": "What does Scripture teach about the nature of God's love?",
        "max_biblical": 3,
        "max_docs": 2,
        "similarity_threshold": 0.7,
        "generation_style": "scholarly"
    }
    
    result = await flow.run(test_query)
    print("Biblical RAG Result:", result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_biblical_rag())