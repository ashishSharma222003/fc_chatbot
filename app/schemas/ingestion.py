from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChunkMetadata(BaseModel):
    """Metadata extracted from a document chunk."""
    next_chunk_id: Optional[str] = Field(None, description="ID of the next logically connected chunk")
    previous_chunk_id: Optional[str] = Field(None, description="ID of the previous logically connected chunk")
    # Dynamic metadata container
    data: Dict[str, Any] = Field(default_factory=dict, description="User-defined metadata based on provided JSON schema")

class ProcessedChunk(BaseModel):
    """A processed chunk of text with its metadata and embedding."""
    chunk_id: str
    text: str
    metadata: ChunkMetadata
    embedding: List[float]
    source_file: str
    date_added: str
