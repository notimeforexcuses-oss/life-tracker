import os
import sqlite3
import json
import hashlib
import numpy as np
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# --- ROBUST PATH LOGIC ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
DB_FILE = project_root / 'brain.db'

# Global client for reuse
_client = None

def _get_genai_client():
    global _client
    if _client is None and API_KEY:
        _client = genai.Client(api_key=API_KEY)
    return _client

def get_db_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def generate_embedding(text_or_list):
    """
    Generates vector embedding(s) using Gemini API.
    Supports single string or list of strings for batching.
    """
    client = _get_genai_client()
    if not text_or_list or not client: return None
    
    try:
        # Standard embedding model
        model_id = "text-embedding-004"
        
        # FALLBACK: If 004 fails in the environment, we use 001 which is confirmed active.
        try:
            if isinstance(text_or_list, list):
                # Batch embedding
                result = client.models.embed_content(
                    model=model_id,
                    contents=text_or_list
                )
                return [emb.values for emb in result.embeddings]
            else:
                # Single embedding
                result = client.models.embed_content(
                    model=model_id,
                    contents=text_or_list
                )
                return result.embeddings[0].values
        except Exception as e:
            if "404" in str(e):
                model_id = "models/gemini-embedding-001"
                if isinstance(text_or_list, list):
                    result = client.models.embed_content(model=model_id, contents=text_or_list)
                    return [emb.values for emb in result.embeddings]
                else:
                    result = client.models.embed_content(model=model_id, contents=text_or_list)
                    return result.embeddings[0].values
            raise e
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None

def update_vector_index(target_id, target_type, text, conn=None):
    """
    Updates or inserts the semantic vector for a specific item.
    Uses binary storage (BLOB) for the embedding.
    """
    if not text: return
    
    # Create content hash
    content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    local_conn = None
    try:
        # We ALWAYS use a local connection if none provided to avoid sharing 
        # cursor state across different transaction contexts which can lead to locks.
        if conn is None:
            local_conn = get_db_connection()
            db_to_use = local_conn
        else:
            db_to_use = conn
            
        cursor = db_to_use.cursor()
        
        # Check existing entry
        cursor.execute("SELECT content_hash FROM semantic_index WHERE target_id=? AND target_type=?", (target_id, target_type))
        row = cursor.fetchone()
        
        # If content hasn't changed, skip
        if row and row['content_hash'] == content_hash:
            return 
            
        # Generate new embedding (EXTERNAL API CALL - can hang or fail)
        try:
            vector = generate_embedding(text)
        except Exception as e:
            print(f"   [Vector Error] API Failure for {target_type} #{target_id}: {e}")
            return

        if vector:
            # Convert to binary for efficient storage
            vector_blob = np.array(vector, dtype=np.float32).tobytes()
            updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if row:
                cursor.execute("""
                    UPDATE semantic_index 
                    SET content_hash=?, embedding=?, updated_at=? 
                    WHERE target_id=? AND target_type=?
                """, (content_hash, sqlite3.Binary(vector_blob), updated_at, target_id, target_type))
            else:
                cursor.execute("""
                    INSERT INTO semantic_index (target_id, target_type, content_hash, embedding, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (target_id, target_type, content_hash, sqlite3.Binary(vector_blob), updated_at))
                
            db_to_use.commit()
            print(f"   [Vector] Indexed {target_type} #{target_id}")
        else:
            print(f"   [Vector] Failed to embed {target_type} #{target_id}")

    except Exception as e:
        print(f"   [Vector Error] Database Failure for {target_type} #{target_id}: {e}")
    finally:
        if local_conn:
            local_conn.close()

def search_vectors(query, target_type=None, limit=5, min_score=0.0):
    """
    Performs a semantic search using cosine similarity.
    Optimized to handle binary embeddings and optional filtering.
    """
    query_vec = generate_embedding(query)
    if not query_vec: return []
    
    query_vec = np.array(query_vec, dtype=np.float32)
    norm_query = np.linalg.norm(query_vec)
    if norm_query == 0: return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "SELECT target_id, target_type, embedding FROM semantic_index"
    params = []
    if target_type:
        sql += " WHERE target_type=?"
        params.append(target_type)
        
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        try:
            # Handle both JSON (legacy) and Binary (new)
            raw_emb = row['embedding']
            if isinstance(raw_emb, bytes):
                vec = np.frombuffer(raw_emb, dtype=np.float32)
            else:
                # Fallback for old JSON data
                vec = np.array(json.loads(raw_emb), dtype=np.float32)
                
            norm_vec = np.linalg.norm(vec)
            if norm_vec == 0: continue
            
            # Cosine Similarity
            similarity = np.dot(query_vec, vec) / (norm_query * norm_vec)
            
            if similarity >= min_score:
                results.append({
                    'id': row['target_id'],
                    'type': row['target_type'],
                    'score': float(similarity)
                })
        except Exception as e:
            continue
            
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def get_vector_stats():
    """
    Returns statistics on vector coverage vs total items.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = []
    tables = {
        'note': 'notes',
        'journal': 'journal_entries',
        'project': 'projects',
        'goal': 'goals',
        'contact': 'contacts',
        'task': 'tasks',
        'workout': 'workouts',
        'interaction': 'interactions',
        'timeline': 'timeline_blocks',
        'exercise': 'exercises',
        'transaction': 'transactions',
        'area': 'areas'
    }
    
    for type_name, table_name in tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM semantic_index WHERE target_type=?", (type_name,))
            vectored = cursor.fetchone()[0]
            stats.append(f"{type_name.title()}: {vectored}/{total} indexed")
        except:
            stats.append(f"{type_name.title()}: Table error")
        
    conn.close()
    return "\n".join(stats)

def backfill_vectors(limit=20):
    """
    Finds un-indexed items and generates vectors in batches.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = {
        'note': ('notes', 'COALESCE(title,"") || "\n" || COALESCE(content,"") || "\n" || COALESCE(tags,"")'),
        'journal': ('journal_entries', 'COALESCE(date,"") || "\n" || COALESCE(content,"") || "\n" || COALESCE(tags,"")'),
        'project': ('projects', 'COALESCE(title,"") || "\n" || COALESCE(description,"")'),
        'goal': ('goals', 'COALESCE(title,"") || "\n" || COALESCE(description,"")'),
        'contact': ('contacts', 'COALESCE(name,"") || "\n" || COALESCE(notes,"") || "\n" || COALESCE(organization,"")'),
        'task': ('tasks', 'COALESCE(title,"") || "\n" || COALESCE(status,"")'),
        'workout': ('workouts', 'COALESCE(type,"") || "\n" || COALESCE(notes,"")'),
        'interaction': ('interactions', 'COALESCE(notes,"")'),
        'timeline': ('timeline_blocks', 'COALESCE(activity,"")'),
        'exercise': ('exercises', 'COALESCE(name,"")'),
        'transaction': ('transactions', 'COALESCE(description,"") || " " || COALESCE(category,"")'),
        'area': ('areas', 'COALESCE(name,"")')
    }
    
    processed = 0
    log = []
    
    try:
        for type_name, (table_name, text_col) in tables.items():
            if processed >= limit: break
            
            sql = f"""
                SELECT t.id, {text_col} as text 
                FROM {table_name} t
                LEFT JOIN semantic_index s ON t.id = s.target_id AND s.target_type = ?
                WHERE s.id IS NULL
                LIMIT ?
            """
            cursor.execute(sql, (type_name, limit - processed))
            rows = cursor.fetchall()
            
            if not rows: continue
            
            # Prepare batch for API
            batch_texts = []
            batch_meta = []
            for row in rows:
                text = row['text']
                if text and len(text.strip()) > 0:
                    # Truncate text to avoid API limits (approx 8k tokens, safe limit here)
                    batch_texts.append(text[:10000])
                    batch_meta.append((row['id'], type_name, text))
            
            if batch_texts:
                vectors = generate_embedding(batch_texts)
                if vectors:
                    for i, vector in enumerate(vectors):
                        target_id, t_type, full_text = batch_meta[i]
                        # Use binary update logic (manually to avoid repeated API calls)
                        vector_blob = np.array(vector, dtype=np.float32).tobytes()
                        content_hash = hashlib.md5(full_text.encode('utf-8')).hexdigest()
                        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        cursor.execute("""
                            INSERT INTO semantic_index (target_id, target_type, content_hash, embedding, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (target_id, t_type, content_hash, sqlite3.Binary(vector_blob), updated_at))
                        
                        log.append(f"Indexed {t_type} #{target_id}")
                        processed += 1
                    conn.commit()
                else:
                    log.append(f"Batch failed for {type_name}")
                    
    except Exception as e:
        log.append(f"Backfill Error: {e}")
    finally:
        conn.close()

    if not log: return "All items are already indexed."
    return f"Backfill Complete ({processed} items):\n" + "\n".join(log)

def delete_vector_index(target_id, target_type):
    """
    Manually removes a vector from the index.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM semantic_index WHERE target_id=? AND target_type=?", (target_id, target_type))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return f"Deleted {count} vector(s) for {target_type} #{target_id}."

