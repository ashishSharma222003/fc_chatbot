import asyncio
import os
from app.services.ingestion_service import IngestionService
from dotenv import load_dotenv

# Mock settings if not running with full env
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in env. Please set it to run this script.")

async def main():
    # Initialize service
    ingestion_service = IngestionService()
    
    # Sample text
    text = """
    The Apollo program was a mocked U.S. human spaceflight program carried out by NASA. 
    It succeeded in preparing and landing the first humans on the Moon from 1968 to 1972.
    It was first conceived during the Eisenhower administration in 1960.
    """
    
    # Define metadata schema (JSON Schema format)
    metadata_schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "entities": {
                "type": "array",
                "items": {"type": "string"}
            },
            "year": {"type": "integer"}
        },
        "required": ["topic", "entities"]
    }
    
    print("Processing text...")
    try:
        chunks = await ingestion_service.process_text(
            text=text, 
            source_file="apollo_history.txt", 
            metadata_schema=metadata_schema
        )
        
        print(f"Processed {len(chunks)} chunks.")
        
        for chunk in chunks:
            print(f"\n--- Chunk {chunk.chunk_id} ---")
            print(f"Text: {chunk.text[:50]}...")
            print(f"Metadata: {chunk.metadata.data}")
            print(f"Prev ID: {chunk.metadata.previous_chunk_id}")
            print(f"Next ID: {chunk.metadata.next_chunk_id}")
            print(f"Embedding Len: {len(chunk.embedding)}")
            
    except Exception as e:
        print(f"Error processing text: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
