import os
import csv
import json
import uuid
import pandas as pd
from datetime import datetime
from openai import OpenAI

API_KEY = "sk-ktaiiqxmiepstghsghnmejwvnrowoqhsfawgpikrounftvxw"
BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "Pro/BAAI/bge-m3"

class SimpleVectorDB:
    def __init__(self):
        self.assets = []
        self.chunks = []
        self.vectors = []

    def add_asset(self, asset):
        self.assets.append(asset)

    def add_chunk(self, chunk, vector):
        self.chunks.append(chunk)
        self.vectors.append(vector)

    def search_vectors(self, query_vector, top_k, filter_fn=None):
        scores = []
        for i, vec in enumerate(self.vectors):
            if filter_fn and not filter_fn(self.chunks[i]):
                continue
            sim = cosine_sim(query_vector, vec)
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self.chunks[i], score) for i, score in scores[:top_k]]

def cosine_sim(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot / (norm_a * norm_b + 1e-10)

def get_client():
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)

def get_embedding(text, client):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def load_assets(csv_path):
    df = pd.read_csv(csv_path)
    assets = {}
    for _, row in df.iterrows():
        acl_groups = row['acl_groups'].split(',') if isinstance(row['acl_groups'], str) else []
        assets[row['asset_id']] = {
            'asset_id': row['asset_id'],
            'source_path': row['source_path'],
            'doc_type': row['doc_type'],
            'version': int(row['version']),
            'updated_at': row['updated_at'],
            'acl_groups': acl_groups,
            'expiry': row['expiry']
        }
    return assets

def chunk_text(text, asset_id, chunk_size=200):
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    section_title = "General"

    for line in lines:
        if line.strip():
            stripped = line.strip()
            is_bullet = stripped.startswith('-') or stripped.startswith('*') or stripped.startswith('•')
            is_title = False
            if not is_bullet:
                is_title = (
                    stripped.isupper() or
                    (len(stripped) < 60 and not stripped.endswith('.') and not stripped.endswith(',') and not stripped.endswith(';')) or
                    (len(stripped) < 50 and stripped.endswith(':'))
                )
            if is_title and len(stripped) > 3:
                section_title = stripped

            current_chunk.append(line)
            current_size += len(line)
            if current_size >= chunk_size:
                chunk_id = str(uuid.uuid4())[:8]
                chunks.append({
                    'chunk_id': chunk_id,
                    'asset_id': asset_id,
                    'text': ' '.join(current_chunk),
                    'page': -1,
                    'section_title': section_title,
                    'section_path': f"{asset_id}/{section_title}"
                })
                current_chunk = []
                current_size = 0

    if current_chunk:
        chunk_id = str(uuid.uuid4())[:8]
        chunks.append({
            'chunk_id': chunk_id,
            'asset_id': asset_id,
            'text': ' '.join(current_chunk),
            'page': -1,
            'section_title': section_title,
            'section_path': f"{asset_id}/{section_title}"
        })

    return chunks

def ingest(docs_dir, assets_csv, db_path='vector_db.json'):
    client = get_client()
    db = SimpleVectorDB()

    assets = load_assets(assets_csv)

    for asset_id, asset in assets.items():
        source_path = os.path.join(os.path.dirname(assets_csv), asset['source_path'])
        if not os.path.exists(source_path):
            print(f"Warning: {source_path} not found")
            continue

        with open(source_path, 'r', encoding='utf-8') as f:
            text = f.read()

        db.add_asset(asset)

        chunks = chunk_text(text, asset_id)
        for chunk in chunks:
            vector = get_embedding(chunk['text'], client)
            db.add_chunk(chunk, vector)

    db_data = {
        'assets': db.assets,
        'chunks': db.chunks,
        'vectors': db.vectors
    }
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db_data, f)

    print(f"Ingestion complete: {len(db.assets)} assets, {len(db.chunks)} chunks")
    return db

if __name__ == "__main__":
    import sys
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "take_home_dataset/docs"
    assets_csv = sys.argv[2] if len(sys.argv) > 2 else "take_home_dataset/assets.csv"
    ingest(docs_dir, assets_csv)
