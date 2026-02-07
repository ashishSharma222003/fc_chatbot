import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.memory_service import MemoryService

def main():
    # Load env vars
    load_dotenv()
    
    if not os.getenv("PINECONE_API_KEY") or not os.getenv("PINECONE_INDEX_NAME"):
        print("Please set PINECONE_API_KEY and PINECONE_INDEX_NAME in .env")
        return

    print("Initializing Memory Service...")
    memory_service = MemoryService()
    
    user_id = "user_123"
    session_id = "session_abc"
    
    # 1. Add Memories
    print("\n--- Adding Memories ---")
    texts = [
        "My favorite color is blue.",
        "I am looking for sustainable fashion brands.",
        "I previously bought a recycled cotton t-shirt."
    ]
    
    for text in texts:
        result = memory_service.add_memory(text, user_id, session_id)
        print(f"Added memory: {result['id']}")

    # 2. Search Memories
    print("\n--- Searching Memories ---")
    queries = [
        "What do I like?",
        "fashion preferences"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = memory_service.search_memory(query, user_id, top_k=2)
        for res in results:
            print(f"  - [{res['score']:.4f}] {res['text']} (Session: {res['metadata'].get('session_id')})")

if __name__ == "__main__":
    main()
