import os
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.session import Session
from models.pdf_chunk import PdfChunk
from core.utils.gcp_utils import  generate_presigned_url
from core.settings import config
from openai import OpenAI
import PyPDF2
import requests
from uuid import uuid4
from datetime import datetime
import time
import random
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import openai
import time
import asyncio
import fitz  
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from sqlalchemy import text
from typing import List



client = OpenAI()
PDF_DOWNLOAD_DIR = "pdf_download"




def normalize_path(path: str) -> str:
    """Convert Windows or mixed paths to Unix-style paths with forward slashes."""
    return str(Path(path)).replace("\\", "/")




@contextmanager
def timer(description: str):
    start = time.time()
    yield
    end = time.time()
    print(f" {description}: {end - start:.2f} seconds")




def extract_text_fast(pdf_path: str) -> str:
    """Ultra-fast PDF text extraction using PyMuPDF"""
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_text = page.get_text()
        text += page_text + "\n"
    doc.close()
    return text




def bulk_insert_chunks_fast(chunks: List[str], embeddings: List[List[float]], 
                           session_id: str, pdf_path: str, db: Session):
    """Ultra-fast bulk insert using SQLAlchemy Core"""
    insert_data = []
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        insert_data.append({
            'chunk_id': str(uuid4()),
            'session_id': session_id,
            'pdf_path': pdf_path,
            'chunk_text': chunk_text,
            'embedding': embedding,
            'chunk_index': i,
            'created_at': datetime.utcnow()
        })
    
    db.bulk_insert_mappings(PdfChunk, insert_data)
    db.commit()




class EmbeddingOptimizer:
    def __init__(self, client, max_retries=3, base_delay=1.0):
        self.client = client
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.performance_stats = []
    

    def get_adaptive_batch_size(self, total_chunks: int, recent_performance: List[float]) -> int:
        """Dynamically adjust batch size based on recent API performance"""
        if not recent_performance:
            # Initial batch size based on document size
            if total_chunks <= 50:
                return 15
            elif total_chunks <= 200:
                return 20
            elif total_chunks <= 500:
                return 25
            else:
                return 30
        
        # If recent batches are slow, reduce batch size
        avg_time_per_chunk = sum(recent_performance) / len(recent_performance)
        
        if avg_time_per_chunk > 0.5:  # If taking more than 0.5s per chunk
            return max(10, total_chunks // 50)  # Smaller batches
        elif avg_time_per_chunk < 0.1:  # If very fast
            return min(40, total_chunks // 10)  # Larger batches
        else:
            return 20  # Default
    

    async def generate_batch_with_retry(self, batch_chunks: List[str], 
                                      batch_num: int, max_time_per_chunk: float = 0.3) -> List[List[float]]:
        """Generate embeddings for a batch with retry logic and timeout detection"""
        
        for attempt in range(self.max_retries + 1):
            batch_start = time.time()
            
            try:
                print(f"Batch {batch_num}: Attempt {attempt + 1}, {len(batch_chunks)} chunks")
                
                # Set timeout based on batch size (max 0.3s per chunk + 5s buffer)
                timeout = len(batch_chunks) * max_time_per_chunk + 5
                
                # Use asyncio for non-blocking call with timeout
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    try:
                        response = await asyncio.wait_for(
                            loop.run_in_executor(
                                executor,
                                lambda: self.client.embeddings.create(
                                    input=batch_chunks,
                                    model="text-embedding-3-small"  #  Fastest OpenAI model
                                )
                            ),
                            timeout=timeout
                        )
                        
                        batch_time = time.time() - batch_start
                        time_per_chunk = batch_time / len(batch_chunks)
                        
                        # Track performance
                        self.performance_stats.append(time_per_chunk)
                        if len(self.performance_stats) > 10:  # Keep only recent 10 batches
                            self.performance_stats.pop(0)
                        
                        print(f" Batch {batch_num} completed in {batch_time:.2f}s "
                              f"({time_per_chunk:.3f}s per chunk)")
                        
                        return [item.embedding for item in response.data]
                        
                    except asyncio.TimeoutError:
                        batch_time = time.time() - batch_start
                        print(f" Batch {batch_num} timed out after {batch_time:.2f}s "
                              f"(expected max {timeout:.1f}s)")
                        raise
                
            except (asyncio.TimeoutError, openai.RateLimitError, openai.APITimeoutError) as e:
                if attempt < self.max_retries:
                    # Exponential backoff with jitter
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f" Batch {batch_num} failed ({type(e).__name__}), retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    print(f" Batch {batch_num} failed after {self.max_retries + 1} attempts")
                    raise
            
            except Exception as e:
                print(f" Batch {batch_num} unexpected error: {str(e)}")
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise





async def generate_embeddings_resilient(chunks: List[str], client) -> List[List[float]]:
    """Resilient embedding generation with adaptive batching and retry logic"""
    
    optimizer = EmbeddingOptimizer(client)
    all_embeddings = []
    
    i = 0
    batch_num = 1
    
    while i < len(chunks):
        # Get adaptive batch size based on recent performance
        batch_size = optimizer.get_adaptive_batch_size(len(chunks), optimizer.performance_stats)
        
        # Don't exceed remaining chunks
        batch_size = min(batch_size, len(chunks) - i)
        
        batch_chunks = chunks[i:i + batch_size]
        
        print(f" Using batch size {batch_size} for batch {batch_num}/{(len(chunks) + batch_size - 1)//batch_size}")
        
        try:
            batch_embeddings = await optimizer.generate_batch_with_retry(
                batch_chunks, batch_num
            )
            all_embeddings.extend(batch_embeddings)
            i += batch_size
            batch_num += 1
            
        except Exception as e:
            # If batch completely fails, try with smaller batch size
            print(f"Batch failed, trying with smaller chunks...")
            if batch_size > 5:
                # Try with half the batch size
                smaller_batch_size = max(5, batch_size // 2)
                batch_chunks = chunks[i:i + smaller_batch_size]
                
                try:
                    batch_embeddings = await optimizer.generate_batch_with_retry(
                        batch_chunks, batch_num, max_time_per_chunk=0.5  # More lenient timeout
                    )
                    all_embeddings.extend(batch_embeddings)
                    i += smaller_batch_size
                    batch_num += 1
                    continue
                except Exception:
                    pass
            
            # If all else fails, process one by one
            print(f"Falling back to individual processing for chunk {i}")
            try:
                single_embedding = await optimizer.generate_batch_with_retry(
                    [chunks[i]], batch_num, max_time_per_chunk=1.0
                )
                all_embeddings.extend(single_embedding)
                i += 1
                batch_num += 1
            except Exception as final_e:
                print(f"Complete failure on chunk {i}: {final_e}")
                raise HTTPException(status_code=500, detail=f"Failed to generate embedding for chunk {i}")
    
    # Print performance summary
    if optimizer.performance_stats:
        avg_performance = sum(optimizer.performance_stats) / len(optimizer.performance_stats)
        print(f"Average performance: {avg_performance:.3f}s per chunk")
    
    return all_embeddings





async def start_chat_session_resilient(pdf_path: str, db: Session):
    """Resilient version with adaptive batching and retry logic"""
    total_start = time.time()
    print(f"Starting RESILIENT chat session for PDF: {pdf_path}")

    if not pdf_path.startswith("users/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid path format – must start with 'users/'"
        )
    
    parts = pdf_path.split("/", 3)
    if len(parts) < 3 or parts[0] != "users":
        raise HTTPException(
            status_code=400,
            detail="Invalid path – user segment missing"
        )
    
    if not os.path.exists(PDF_DOWNLOAD_DIR):
        os.makedirs(PDF_DOWNLOAD_DIR)
    
    pdf_path = normalize_path(pdf_path)
    if not pdf_path.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file path: must be a PDF")
    
    pdf_filename = f"{uuid4()}.pdf"
    local_path = os.path.join(PDF_DOWNLOAD_DIR, pdf_filename)
    
    # PDF Download
    with timer("PDF Download from GCS"):
        try:
            presigned_url = generate_presigned_url(pdf_path)
            response = requests.get(presigned_url)
            response.raise_for_status()
            print(f"Downloaded PDF size: {len(response.content)} bytes")
            with open(local_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to download PDF: {str(e)}")
    
    # Database Session Creation
    with timer("Database Session Creation"):
        session = Session(session_id=uuid4(), pdf_path=pdf_path, created_at=datetime.utcnow())
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"Created session: {session.session_id}")
    
    try:
        # Ultra-Fast PDF Text Extraction
        with timer("Ultra-Fast PDF Text Extraction (PyMuPDF)"):
            text = extract_text_fast(local_path)
            print(f"Total extracted text length: {len(text)} characters")
        
        # Text Chunking
        with timer("Text Chunking"):
            chunk_size = 1000
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
            chunks = [chunk for chunk in chunks if chunk.strip()]
            print(f"Created {len(chunks)} chunks")
        
        # Resilient Batch Embedding Generation
        with timer("Resilient Batch Embedding Generation"):
            all_embeddings = await generate_embeddings_resilient(chunks, client)
        
        # Ultra-Fast Bulk Database Insert
        with timer("Ultra-Fast Bulk Database Insert"):
            bulk_insert_chunks_fast(chunks, all_embeddings, session.session_id, pdf_path, db)
            print(f"Inserted {len(chunks)} chunks to database")
        
    except Exception as e:
        print(f"PDF processing error: {str(e)}")
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        with timer("File Cleanup"):
            try:
                if os.path.exists(local_path):
                    os.remove(local_path)
                    print(f" Deleted local file: {local_path}")
            except Exception as e:
                print(f" Warning: Failed to delete PDF file {local_path}: {str(e)}")
    
    total_time = time.time() - total_start
    print(f"RESILIENT TOTAL TIME: {total_time:.2f} seconds")
    
    return {"session_id": str(session.session_id), "message": "Chat session started"}






async def chat_with_pdf_timed(session_id: str, pdf_path: str, query: str, db: Session, top_k: int = 5):
    """Query PDF chunks with detailed timing analysis."""
    total_start = time.time()
    print(f" Starting chat with PDF: {pdf_path}, Session: {session_id}")
    print(f"Query: {query}")
    
    pdf_path = normalize_path(pdf_path)
    
    # TIMING: Session Validation
    with timer("Session Validation"):
        session = db.query(Session).filter(
            Session.session_id == session_id, 
            Session.pdf_path == pdf_path
        ).first()
        if not session:
            print(f" Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session or PDF not found")
        print(f" Session validated: {session_id}")
    
    # TIMING: Query Embedding Generation
    with timer("Query Embedding Generation"):
        try:
            response = client.embeddings.create(
                input=query, 
                model="text-embedding-3-small"  # Still using old model here
            )
            query_embedding = response.data[0].embedding
            print(f"Generated query embedding, length: {len(query_embedding)}")
        except Exception as e:
            print(f"Query embedding error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating query embedding: {str(e)}")
    
    # TIMING: Vector Similarity Search
    with timer("Vector Similarity Search"):
        try:
            chunks = db.query(PdfChunk).filter(
                PdfChunk.session_id == session_id
            ).order_by(
                PdfChunk.embedding.cosine_distance(query_embedding)
            ).limit(top_k).all()
            
            if not chunks:
                print(" No chunks found for session")
                raise HTTPException(status_code=404, detail="No relevant chunks found")
            print(f" Retrieved {len(chunks)} chunks")
            
            # Print similarity scores for debugging
            for i, chunk in enumerate(chunks):
                # Note: This is approximate since we can't easily get the actual distance
                print(f"  Chunk {i+1}: Index {chunk.chunk_index}, Length: {len(chunk.chunk_text)} chars")
                
        except Exception as e:
            print(f" Vector search error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving chunks: {str(e)}")
    
    # TIMING: Context Preparation
    with timer("Context Preparation"):
        context = "\n".join(f"Chunk {chunk.chunk_index}: {chunk.chunk_text}" for chunk in chunks)
        print(f"Context length: {len(context)} characters")
    
    # TIMING: LLM Response Generation
    with timer("LLM Response Generation"):
        try:
            prompt = f"Based on the following PDF content, answer the query: {query}\n\nContent:\n{context}"
            print(f"Prompt length: {len(prompt)} characters")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            answer = response.choices[0].message.content.strip()
            print(f"Generated LLM response: {answer[:100]}...")
            
        except Exception as e:
            print(f" LLM error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
    
    # TIMING: Response Preparation
    with timer("Response Preparation"):
        result = {
            "answer": answer,
            "relevant_chunks": [
                {"chunk_index": chunk.chunk_index, "chunk_text": chunk.chunk_text}
                for chunk in chunks
            ]
        }
    
    total_time = time.time() - total_start
    print(f"TOTAL CHAT TIME: {total_time:.3f} seconds")
    
    return result






async def end_chat_session_timed(session_id: str, user_id: str, db: Session):
    """End a chat session by deleting it and its associated chunks."""
    print(f"Ending session: {session_id} for user: {user_id}")
    session = db.query(Session).filter(Session.session_id == session_id).first()
    if not session:
        print(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    # Verify session belongs to user
    if not session.pdf_path.startswith(f"users/{user_id}/"):
        print(f"Unauthorized attempt to delete session {session_id} by user {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access to session")
    try:
        # Delete chunks first using raw SQL (fast)
        db.execute(text("DELETE FROM pdf_chunks WHERE session_id = :session_id"), {"session_id": session_id})
        # Delete session using raw SQL
        db.execute(text("DELETE FROM sessions WHERE session_id = :session_id"), {"session_id": session_id})
        db.commit()
        print(f"Session {session_id} deleted successfully")
    except Exception as e:
        print(f"Error deleting session {session_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
    return {"message": f"Session {session_id} ended successfully"}