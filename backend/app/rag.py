import numpy as np
from sqlalchemy.orm import Session
from openai import OpenAI
from backend.app.config import OPENAI_API_KEY
from backend.app.db import KnowledgeChunkModel

def get_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)

def generate_embedding(text: str) -> list[float]:
    """Generates a 1536-dimensional embedding using OpenAI text-embedding-3-small."""
    if not OPENAI_API_KEY:
        # Return mock embedding for testing
        return [0.1] * 1536
        
    client = get_openai_client()
    try:
        response = client.embeddings.create(
            input=[text.replace("\n", " ")],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return mock embedding as fallback
        return [0.1] * 1536

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Chunks text into overlapping blocks while keeping words intact."""
    words = text.split()
    chunks = []
    current_words = []
    current_length = 0
    
    for word in words:
        current_words.append(word)
        current_length += len(word) + 1  # count the word plus space
        if current_length >= chunk_size:
            chunks.append(" ".join(current_words))
            # Keep overlap words
            overlap_words = []
            overlap_len = 0
            for w in reversed(current_words):
                if overlap_len + len(w) + 1 <= overlap:
                    overlap_words.insert(0, w)
                    overlap_len += len(w) + 1
                else:
                    break
            current_words = overlap_words
            current_length = overlap_len
            
    if current_words:
        chunks.append(" ".join(current_words))
        
    # Filter out empty or tiny chunks
    return [c for c in chunks if len(c.strip()) > 30]

def ingest_document(db: Session, text: str, file_name: str, role_type: str) -> int:
    """Chunks, embeds, and saves document content to the database."""
    chunks = chunk_text(text)
    count = 0
    for chunk in chunks:
        embedding = generate_embedding(chunk)
        # Convert float list to binary
        embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
        
        db_chunk = KnowledgeChunkModel(
            chunk_text=chunk,
            file_name=file_name,
            role_type=role_type,
            embedding=embedding_blob
        )
        db.add(db_chunk)
        count += 1
        
    db.commit()
    return count

def retrieve_context(db: Session, query: str, role_type: str, limit: int = 3) -> list[dict]:
    """Retrieves top K similar chunks from the SQLite DB using NumPy cosine similarity."""
    # Query embedding
    query_emb = np.array(generate_embedding(query), dtype=np.float32)
    
    # Retrieve all chunks for this specific role
    chunks = db.query(KnowledgeChunkModel).filter(KnowledgeChunkModel.role_type == role_type).all()
    if not chunks:
        return []
        
    # Extract chunk embeddings
    chunk_embeddings = []
    valid_chunks = []
    
    for chunk in chunks:
        try:
            emb = np.frombuffer(chunk.embedding, dtype=np.float32)
            if emb.shape[0] == 1536: # Standard OpenAI dimension
                chunk_embeddings.append(emb)
                valid_chunks.append(chunk)
        except Exception as e:
            print(f"Error parsing embedding for chunk {chunk.id}: {e}")
            
    if not chunk_embeddings:
        return []
        
    # Compute cosine similarity
    # Matrix of shape (N, 1536)
    matrix = np.array(chunk_embeddings)
    
    # Calculate similarity scores
    # Dot product
    dot_products = np.dot(matrix, query_emb)
    # Norms
    matrix_norms = np.linalg.norm(matrix, axis=1)
    query_norm = np.linalg.norm(query_emb)
    
    # Handle division by zero
    norms_prod = matrix_norms * query_norm
    norms_prod[norms_prod == 0] = 1e-9
    
    similarities = dot_products / norms_prod
    
    # Get top K indices
    top_indices = np.argsort(similarities)[::-1][:limit]
    
    results = []
    for idx in top_indices:
        score = float(similarities[idx])
        chunk = valid_chunks[idx]
        results.append({
            "chunk_text": chunk.chunk_text,
            "file_name": chunk.file_name,
            "score": score
        })
        
    return results
