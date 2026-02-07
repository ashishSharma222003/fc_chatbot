from typing import List, Dict, Any, Optional
import numpy as np
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.schemas.ingestion import ProcessedChunk

class VectorStore:
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
        
        # Initialize embedding model (Same as ingestion for consistency)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def upsert_chunks(self, chunks: List[ProcessedChunk], namespace: str = "knowledge_base"):
        """
        Upserts processed chunks into Pinecone.
        """
        vectors = []
        for chunk in chunks:
            # Flatten metadata for Pinecone compatibility (no nested dicts preferred, but check support)
            # We'll store the 'data' dict as a JSON string or flattened fields if needed.
            # For now, storing 'data' directly assuming Pinecone metadata support.
            
            metadata = {
                "text": chunk.text,
                "source_file": chunk.source_file,
                "date_added": chunk.date_added,
                "previous_chunk_id": chunk.metadata.previous_chunk_id or "",
                "next_chunk_id": chunk.metadata.next_chunk_id or "",
                "type": "document_chunk"
            }
            # Merge dynamic metadata
            for k, v in chunk.metadata.data.items():
                if isinstance(v, (str, int, float, bool)):
                     metadata[k] = v
                else:
                    # Convert complex types to string
                    metadata[k] = str(v)

            vectors.append((chunk.chunk_id, chunk.embedding, metadata))
        
        # Batch upsert (Pinecone recommends batches of 100)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)

    def search(self, query: str, top_k: int = 5, namespace: str = "knowledge_base", filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Basic semantic search.
        """
        query_embedding = self.embedding_model.encode(query).tolist()
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
            filter=filter
        )
        
        return [
            {
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "metadata": match.metadata
            }
            for match in results.matches
        ]

    def mmr_search(self, query: str, top_k: int = 5, diversity: float = 0.5, namespace: str = "knowledge_base", filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Maximal Marginal Relevance (MMR) search to optimize for similarity and diversity.
        diversity: 0.0 (max similarity) to 1.0 (max diversity).
        """
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Fetch more candidates than top_k to re-rank
        fetch_k = top_k * 4
        results = self.index.query(
            vector=query_embedding,
            top_k=fetch_k,
            include_values=True, # Need vectors for MMR
            include_metadata=True,
            namespace=namespace,
            filter=filter
        )
        
        if not results.matches:
            return []

        # Extract vectors and metadata
        candidate_vectors = [match.values for match in results.matches]
        candidate_ids = [match.id for match in results.matches]
        candidate_metadata = [match.metadata for match in results.matches]
        
        # Calculate MMR
        selected_indices = self._calculate_mmr(
            query_embedding, 
            candidate_vectors, 
            top_k, 
            diversity
        )
        
        return [
            {
                "id": candidate_ids[i],
                "score": 0.0, # MMR doesn't yield a direct similarity score in the same way
                "text": candidate_metadata[i].get("text", ""),
                "metadata": candidate_metadata[i]
            }
            for i in selected_indices
        ]

    def _calculate_mmr(self, query_embedding: List[float], candidate_vectors: List[List[float]], top_k: int, lambda_param: float) -> List[int]:
        """
        Core MMR calculation.
        """
        if not candidate_vectors:
            return []

        # Convert to numpy for efficiency
        query_vec = np.array(query_embedding).reshape(1, -1)
        candidate_matrix = np.array(candidate_vectors)
        
        # Cosine similarity between query and candidates
        # (Assuming normalized vectors, dot product = cosine similarity)
        # Using dot product for speed (SentenceTransformers produces normalized vectors usually)
        # Safe bet: compute cosine similarity properly
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Sim(query, candidates)
        sim_query_candidates = cosine_similarity(query_vec, candidate_matrix)[0]
        
        # Sim(candidates, candidates)
        sim_candidate_candidate = cosine_similarity(candidate_matrix, candidate_matrix)
        
        selected_indices = []
        candidate_indices = list(range(len(candidate_vectors)))
        
        for _ in range(min(top_k, len(candidate_vectors))):
            best_mmr = -float("inf")
            best_idx = -1
            
            for idx in candidate_indices:
                # Sim with query
                sim_q = sim_query_candidates[idx]
                
                # Max sim with already selected
                if not selected_indices:
                    max_sim_selected = 0
                else:
                    max_sim_selected = max([sim_candidate_candidate[idx][sel_idx] for sel_idx in selected_indices])
                
                # MMR formula: lambda * Sim(Q, D) - (1-lambda) * max(Sim(D, Selected))
                mmr_score = lambda_param * sim_q - (1 - lambda_param) * max_sim_selected
                
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = idx
            
            selected_indices.append(best_idx)
            candidate_indices.remove(best_idx)
            
        return selected_indices
