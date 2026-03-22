import json
from datetime import datetime
from openai import OpenAI

API_KEY = "sk-ktaiiqxmiepstghsghnmejwvnrowoqhsfawgpikrounftvxw"
BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "Pro/BAAI/bge-m3"

class RetrievalSystem:
    def __init__(self, db_path='vector_db.json'):
        self.db_path = db_path
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self._load_db()

    def _load_db(self):
        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assets = {a['asset_id']: a for a in data['assets']}
        self.chunks = data['chunks']
        self.vectors = data['vectors']

    def _cosine_sim(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot / (norm_a * norm_b + 1e-10)

    def _get_embedding(self, text):
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def _is_expired(self, asset):
        expiry = datetime.strptime(asset['expiry'], '%Y-%m-%d')
        return datetime.now() > expiry

    def _has_access(self, asset, user_groups):
        if 'all' in asset['acl_groups']:
            return True
        return any(group in asset['acl_groups'] for group in user_groups)

    def _create_filter(self, user_groups):
        def filter_fn(chunk):
            asset = self.assets.get(chunk['asset_id'])
            if not asset:
                return False
            if self._is_expired(asset):
                return False
            if not self._has_access(asset, user_groups):
                return False
            return True
        return filter_fn

    def retrieve(self, query, user_groups, top_k=5):
        query_vector = self._get_embedding(query)
        filter_fn = self._create_filter(user_groups)

        results = []
        for i, vec in enumerate(self.vectors):
            if not filter_fn(self.chunks[i]):
                continue
            score = self._cosine_sim(query_vector, vec)
            results.append((self.chunks[i], score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'vector_db.json'
    rs = RetrievalSystem(db_path)
    results = rs.retrieve("fire safety", ["design"], top_k=3)
    for chunk, score in results:
        print(f"[{score:.3f}] {chunk['text'][:100]}...")
