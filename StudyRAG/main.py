import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from dotenv import load_dotenv
from inngest.experimental import ai
import uuid
import os
import datetime
import data_loader
from vector_db import QdrantStorage
from custom_types import RAGChunkAndSrc, RAGUpsertResult, RAGSearchResult, RAGQueryResult

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "service": "StudyRAG API"}

inngest_client = inngest.Inngest(
    app_id="study-rag",
    logger=logging.getLogger("uvicorn"),
    is_production=os.getenv("INNGEST_DEV") is None,
    signing_key=os.getenv("INNGEST_SIGNING_KEY"),
    event_key=os.getenv("INNGEST_EVENT_KEY")
)

# Define an Inngest function to handle the "user_message" event
@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest-pdf")
)
async def rag_ingest_pdf(ctx: inngest.Context):
    def _load(ctx: inngest.Context) -> dict:
        # Check if text is provided directly (Cloud/Vercel deployment)
        if "text" in ctx.event.data:
            text = ctx.event.data["text"]
            source_id = ctx.event.data.get("source_id", "uploaded_text")
            chunks = data_loader.chunk_text(text)
            return RAGChunkAndSrc(chunks=chunks, source_id=source_id).model_dump()
            
        # Fallback to local file path (Local development)
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = data_loader.load_and_chunk_pdf(pdf_path)
        return RAGChunkAndSrc(chunks=chunks, source_id=source_id).model_dump()
    

    def _upsert(chunks_and_src: dict) -> dict:
        chunks = chunks_and_src["chunks"]
        source_id = chunks_and_src["source_id"]
        vecs = data_loader.embed_texts(chunks)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}_{i}")) for i in range(len(chunks))]
        payloads = [{"source": source_id, "text": chunks[i]} for i in range(len(chunks))]
        QdrantStorage().upsert(ids, vecs, payloads)
        return RAGUpsertResult(ingested=len(chunks)).model_dump()

    chunks_and_src = await ctx.step.run("load-and-chunk", lambda: _load(ctx))
    ingested = await ctx.step.run("embed-and-upsert", lambda: _upsert(chunks_and_src))
    return ingested

@inngest_client.create_function(
    fn_id="RAG: Query PDF",
    trigger = inngest.TriggerEvent(event="rag/query-pdf") 
)

async def rag_query_pdf_ai(ctx: inngest.Context):
    def _search(question: str, top_k: int = 5) -> dict:
        query_vec = data_loader.embed_texts([question])[0]
        store = QdrantStorage()
        found = store.search(query_vec, top_k)
        return RAGSearchResult(contexts=found["contexts"],sources=found["sources"]).model_dump()
    
    question = ctx.event.data["question"]
    top_k = ctx.event.data.get("top_k", 5)
    found = await ctx.step.run("embed-and-search", lambda: _search(question, top_k))

    context_block = "\n\n".join(f"- {c}" for c in found["contexts"])
    user_content = (
        "Use the following context to answer the question.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "Answer concisely using the context above."
    )

    adapter = ai.openai.Adapter(
        auth_key = os.getenv("OPENROUTER_API_KEY"),
        model = "gpt-4o-mini",
        base_url = "https://openrouter.ai/api/v1"
    )

    res = await ctx.step.ai.infer(
        "llm-answer",
        adapter = adapter,
        body = {
            "max_tokens": 1024,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": "You answer questions based on provided context."},
                {"role": "user", "content": user_content}
            ]
        }

    )

    answer = res["choices"][0]["message"]["content"].strip()
    return {
        "answer":answer,
        "sources":found["sources"],
        "num_contexts":len(found["contexts"])
    }

inngest.fast_api.serve(app, inngest_client, [rag_ingest_pdf, rag_query_pdf_ai])



