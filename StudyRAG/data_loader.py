from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
import os

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

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

def load_and_chunk_pdf(file: str):
    docs = PDFReader().load_data(file=file)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks

def embed_texts(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


