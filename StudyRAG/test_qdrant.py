"""
Test script to verify Qdrant connection
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Qdrant Connection...")
print(f"QDRANT_URL: {os.getenv('QDRANT_URL')}")
print(f"QDRANT_API_KEY: {'*' * 20 if os.getenv('QDRANT_API_KEY') else 'NOT SET'}")
print()

try:
    from vector_db import QdrantStorage
    print("Attempting to connect to Qdrant...")
    storage = QdrantStorage()
    print("✅ Successfully connected to Qdrant!")
    
    # Try to get sources
    sources = storage.get_all_sources()
    print(f"📚 Found {len(sources)} document(s) in the database")
    if sources:
        for source in sources:
            print(f"  • {source}")
    
except ConnectionError as e:
    print(f"❌ Connection Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check your internet connection")
    print("2. Verify QDRANT_URL in .env file")
    print("3. Ensure Qdrant cloud instance is running")
    print("4. Check firewall/proxy settings")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
