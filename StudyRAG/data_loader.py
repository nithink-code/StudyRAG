from openai import OpenAI
from pypdf import PdfReader
from dotenv import load_dotenv
import os
import re

load_dotenv()

# Check if Open Router API key is available
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    # Use Open Router API
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key
    )
    EMBED_MODEL="openai/text-embedding-3-small"
    EMBED_DIM=1536  # Dimension for text-embedding-3-small
else:
    client = OpenAI()
    EMBED_MODEL="text-embedding-3-small"
    EMBED_DIM=1536

def recursive_split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Splits text recursively based on characters, mimicking RecursiveCharacterTextSplitter.
    """
    if not text:
        return []

    # If the text is small enough, return it as a single chunk
    if len(text) <= chunk_size:
        return [text]

    # Split by separators (paragraph, sentence, etc.)
    separators = ["\n\n", "\n", " ", ""]
    
    final_chunks = []
    
    # Very basic recursive implementation
    # We try to split by the largest separator first
    # If a chunk is still too big, we move to the next separator
    
    # This is a simplified version. For now, let's use a simpler approach:
    # Split by full stops or newlines to get sentences/paragraphs
    # Then group them.
    
    # Regex split to keep delimiters
    # Split by sentence endings (.?!) or newlines
    # This is a heuristic.
    
    # Alternatively, just iterate and accumulate.
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > chunk_size and current_chunk:
            final_chunks.append(" ".join(current_chunk))
            
            # reliable overlap Logic
            overlap_words = []
            overlap_len = 0
            # backtrack to get overlap
            # This is complex to get right perfectly without a library, 
            # but we can just simplify for now: no overlap or simple overlap
            
            # Simple approach: start new chunk with last few words?
            # Or just ignore overlap for now to save complexity/bugs
            # Let's try to do a sliding window of words?
            
            current_chunk = []
            current_length = 0
            
        current_chunk.append(word)
        current_length += len(word) + 1
        
    if current_chunk:
        final_chunks.append(" ".join(current_chunk))
        
    return final_chunks

# Better implementation of splitter to ensure we respect chunk_size and overlap
def robust_app_split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    if not text:
        return []
        
    # Standardize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        
        # If we are at the end, just take the rest
        if end >= text_len:
            chunks.append(text[start:])
            break
            
        # Try to find a good breaking point (space) backwards from end
        # to avoid splitting words
        good_end = text.rfind(' ', start, end)
        
        if good_end != -1 and good_end > start:
            end = good_end
            
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start forward, respecting overlap
        start = end - chunk_overlap
        # Ensure we always move forward
        if start <= (end - len(chunk)): 
             start = end # No overlap possible or loop
             
        # Simple fix to ensure progress
        if start < end:
             pass
        else:
             start = end
             
    return chunks

def load_and_chunk_pdf(file: str):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
            
    return robust_app_split_text(text, chunk_size=1000, chunk_overlap=200)

def chunk_text(text: str) -> list[str]:
    return robust_app_split_text(text, chunk_size=1000, chunk_overlap=200)

def embed_texts(texts: list[str]) -> list[list[float]]:
    try:
        response = client.embeddings.create(
            model=EMBED_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"Error embedding texts: {e}")
        return []
