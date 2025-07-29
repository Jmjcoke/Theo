"""
Embedding utilities for EmbeddingGeneratorNode.
Extracted to maintain PocketFlow 150-line limit and handle OpenAI API integration.
"""
import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
import time


class EmbeddingUtils:
    """Utility class for OpenAI embedding generation operations."""
    
    def __init__(self):
        """Initialize OpenAI client configuration"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = 'https://api.openai.com/v1/embeddings'
        self.model = 'text-embedding-ada-002'
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.batch_size = 100  # OpenAI recommended batch size
        
    async def validate_api_config(self) -> bool:
        """Validate OpenAI API configuration"""
        if not self.api_key:
            return False
        if not self.api_key.startswith('sk-'):
            return False
        return True
    
    async def generate_embedding(self, text: str) -> Dict[str, Any]:
        """Generate embedding for a single text string"""
        try:
            if not await self.validate_api_config():
                return {"success": False, "error": "Invalid OpenAI API configuration"}
            
            preprocessed_text = self._preprocess_text(text)
            embedding = await self._call_openai_api([preprocessed_text])
            
            return {
                "success": True,
                "embedding": embedding[0],
                "model": self.model,
                "dimensions": len(embedding[0])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_embeddings_batch(self, chunks: List[Dict[str, Any]], document_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate embeddings for all chunks with batch processing and error handling"""
        embedded_chunks = []
        failed_chunks = []
        
        # Process chunks in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_embedded, batch_failed = await self._process_batch(batch, document_id)
            embedded_chunks.extend(batch_embedded)
            failed_chunks.extend(batch_failed)
        
        return embedded_chunks, failed_chunks
    
    async def _process_batch(self, batch: List[Dict[str, Any]], document_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process a batch of chunks for embedding generation"""
        start_time = time.time()
        embedded_chunks = []
        failed_chunks = []
        
        # Extract and preprocess texts for batch API call
        texts = [self._preprocess_text(chunk['content']) for chunk in batch]
        
        try:
            # Generate embeddings for batch
            embeddings = await self._call_openai_api(texts)
            
            # Pair embeddings with chunks
            for chunk, embedding in zip(batch, embeddings):
                processing_time_ms = int((time.time() - start_time) * 1000)
                embedded_chunk = self._create_embedded_chunk(chunk, embedding, processing_time_ms)
                embedded_chunks.append(embedded_chunk)
                
        except Exception as e:
            # If batch fails, try individual chunks
            for chunk in batch:
                try:
                    individual_start = time.time()
                    preprocessed_text = self._preprocess_text(chunk['content'])
                    embedding = await self._call_openai_api([preprocessed_text])
                    processing_time_ms = int((time.time() - individual_start) * 1000)
                    embedded_chunk = self._create_embedded_chunk(chunk, embedding[0], processing_time_ms)
                    embedded_chunks.append(embedded_chunk)
                except Exception as individual_error:
                    failed_chunk = chunk.copy()
                    failed_chunk['error'] = str(individual_error)
                    failed_chunks.append(failed_chunk)
        
        return embedded_chunks, failed_chunks
    
    async def _call_openai_api(self, texts: List[str]) -> List[List[float]]:
        """Call OpenAI API with retry logic and rate limit handling"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'input': texts
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_base,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            return [item['embedding'] for item in data['data']]
                        
                        elif response.status == 429:  # Rate limit
                            if attempt < self.max_retries - 1:
                                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                                await asyncio.sleep(delay)
                                continue
                            else:
                                raise Exception(f"Rate limit exceeded after {self.max_retries} attempts")
                        
                        else:
                            error_text = await response.text()
                            raise Exception(f"OpenAI API error {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"API timeout after {self.max_retries} attempts")
            
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"API client error: {str(e)}")
        
        raise Exception("Failed to get embeddings after all retry attempts")
    
    def _create_embedded_chunk(self, chunk: Dict[str, Any], embedding: List[float], processing_time_ms: int = 0) -> Dict[str, Any]:
        """Create embedded chunk with proper structure and metadata"""
        embedded_chunk = chunk.copy()
        embedded_chunk['embedding'] = embedding
        embedded_chunk['embedding_metadata'] = {
            'model': self.model,
            'dimensions': len(embedding),
            'generated_at': self.get_timestamp(),
            'api_version': 'v1',
            'processing_time_ms': processing_time_ms
        }
        return embedded_chunk
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for optimal embedding generation"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        # Truncate if too long (OpenAI has token limits)
        if len(text) > 8000:  # Conservative limit
            text = text[:8000]
        return text
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')