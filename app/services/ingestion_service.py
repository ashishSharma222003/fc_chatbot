"""
Ingestion Service

This service manages the processing of uploaded documents.
It handles text extraction, chunking, and preparing data for indexing into the
vector store, ensuring raw files are converted into queryable knowledge.
"""
from typing import List, Dict, Any, Optional
import uuid
from sentence_transformers import SentenceTransformer
from app.services.llm_service import LLMService
from app.schemas.ingestion import ProcessedChunk, ChunkMetadata

from datetime import datetime
import asyncio

class IngestionService:
    def __init__(self):
        self.llm_service = LLMService()
        # Initialize embedding model (lazy loading or at startup)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    async def process_file(self, file_content: bytes, filename: str, metadata_schema: Optional[Dict[str, Any]], system_prompt: str) -> List[ProcessedChunk]:
        """
        Process a file: extract text based on extension and ingest.
        """
        content_str = ""
        if filename.endswith(".txt") or filename.endswith(".md"):
            content_str = file_content.decode("utf-8")
        else:
            # TODO: Add support for PDF, DOCX, etc.
            raise ValueError(f"Unsupported file type: {filename}")
            
        return await self.process_text(content_str, filename, metadata_schema, system_prompt)

    async def process_text(self, text: str, source_file: str, metadata_schema: Optional[Dict[str, Any]], system_prompt: str) -> List[ProcessedChunk]:
        """
        Process text content: chunk, embed, extract metadata, and link.
        """
        chunks = self._chunk_text(text)
        
        # 1. Batch Generate Embeddings (Much faster than loop)
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        # 2. Parallel Metadata Extraction (Concurrent LLM calls)
        async def extract_for_chunk(chunk_text: str):
            if metadata_schema:
                user_prompt = f"Extract metadata from the following text based on the provided schema:\n\n{chunk_text}"
                result,tokens = await self.llm_service.get_structured_response(
                    user_prompt=user_prompt,
                    schema=metadata_schema,
                    system_prompt=system_prompt
                )
                return result,tokens
            return {},{}

        metadata_results = await asyncio.gather(*[extract_for_chunk(chunk) for chunk in chunks])
        
        processed_chunks = []
        
        # 3. Assemble ProcessedChunks
        for i, (chunk_text, embedding, extracted_metadata,tokens) in enumerate(zip(chunks, embeddings, metadata_results)):
            chunk_id = str(uuid.uuid4())
            
            # Create metadata object with links
            metadata = ChunkMetadata(
                next_chunk_id=None, # To be filled
                previous_chunk_id=processed_chunks[-1].chunk_id if i > 0 else None,
                data=extracted_metadata
            )
            
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                metadata=metadata,
                embedding=embedding,
                source_file=source_file,
                date_added=datetime.now().isoformat()
            )
            processed_chunks.append(processed_chunk)

        # Link next_chunk_ids
        for i in range(len(processed_chunks) - 1):
            processed_chunks[i].metadata.next_chunk_id = processed_chunks[i+1].chunk_id
            
        return processed_chunks

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Simple text chunking with overlap.
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
            
        return chunks
