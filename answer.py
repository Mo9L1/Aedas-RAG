import json
import re
from datetime import datetime
from openai import OpenAI

API_KEY = "sk-ktaiiqxmiepstghsghnmejwvnrowoqhsfawgpikrounftvxw"
BASE_URL = "https://api.siliconflow.cn/v1"
LLM_MODEL = "Pro/deepseek-ai/DeepSeek-V3.2"

class AnswerSystem:
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
            model="Pro/BAAI/bge-m3",
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

    def _check_access(self, user_groups):
        available = []
        for asset in self.assets.values():
            if self._is_expired(asset):
                continue
            if not self._has_access(asset, user_groups):
                continue
            available.append(asset)
        return available

    def _get_asset_chunks(self, asset_id):
        return [c for c in self.chunks if c['asset_id'] == asset_id]

    def retrieve(self, query, user_groups, top_k=5):
        query_vector = self._get_embedding(query)
        available_assets = self._check_access(user_groups)
        available_asset_ids = {a['asset_id'] for a in available_assets}

        results = []
        for i, vec in enumerate(self.vectors):
            chunk = self.chunks[i]
            if chunk['asset_id'] not in available_asset_ids:
                continue
            score = self._cosine_sim(query_vector, vec)
            results.append((chunk, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _format_citation(self, chunk, asset):
        return {
            'chunk_id': chunk['chunk_id'],
            'asset_id': chunk['asset_id'],
            'doc_type': asset['doc_type'],
            'section_title': chunk['section_title'],
            'text': chunk['text'][:200]
        }

    def _get_all_relevant(self, query):
        query_vector = self._get_embedding(query)
        results = []
        for i, vec in enumerate(self.vectors):
            chunk = self.chunks[i]
            score = self._cosine_sim(query_vector, vec)
            results.append((chunk, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def answer(self, query, user_groups, top_k=5):
        all_results = self._get_all_relevant(query)
        if not all_results:
            return {'answer': None, 'citations': [], 'refusal_reason': 'no_evidence'}

        available_assets = self._check_access(user_groups)
        available_asset_ids = {a['asset_id'] for a in available_assets}

        accessible_results = [(c, s) for c, s in all_results if c['asset_id'] in available_asset_ids]

        if not accessible_results:
            top_chunk = all_results[0][0]
            top_asset = self.assets.get(top_chunk['asset_id'])
            if self._is_expired(top_asset):
                return {'answer': None, 'citations': [], 'refusal_reason': 'expired'}
            if not self._has_access(top_asset, user_groups):
                return {'answer': None, 'citations': [], 'refusal_reason': 'no_access'}
            return {'answer': None, 'citations': [], 'refusal_reason': 'no_access'}

        if accessible_results[0][1] < 0.5:
            top_chunk = all_results[0][0]
            top_asset = self.assets.get(top_chunk['asset_id'])
            if self._is_expired(top_asset):
                return {'answer': None, 'citations': [], 'refusal_reason': 'expired'}
            if not self._has_access(top_asset, user_groups):
                return {'answer': None, 'citations': [], 'refusal_reason': 'no_access'}
            return {'answer': None, 'citations': [], 'refusal_reason': 'no_evidence'}

        context_parts = []
        citations = []
        for chunk, score in accessible_results[:top_k]:
            asset = self.assets.get(chunk['asset_id'])
            if asset:
                context_parts.append(f"[Source {len(context_parts)+1}]: {chunk['text']}")
                citations.append(self._format_citation(chunk, asset))

        context = "\n\n".join(context_parts)
        prompt = f"""Based on the following sources, answer the question.

Sources:
{context}

Question: {query}

Respond with JSON only:
{{"answer": "your answer text", "cited_texts": ["exact text snippet from sources that support your answer"]}}"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw_response = response.choices[0].message.content

        import json as json_lib
        try:
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json_lib.loads(raw_response[json_start:json_end])
                answer = parsed.get('answer', raw_response)
                cited_texts = parsed.get('cited_texts', [])
            else:
                answer = raw_response
                cited_texts = []
        except:
            answer = raw_response
            cited_texts = []

        verified_citations = []
        for cited_text in cited_texts:
            for chunk, score in accessible_results[:top_k]:
                asset = self.assets.get(chunk['asset_id'])
                if asset and cited_text.strip() in chunk['text']:
                    citation = self._format_citation(chunk, asset)
                    if citation not in verified_citations:
                        verified_citations.append(citation)
                    break

        return {'answer': answer, 'citations': verified_citations, 'refusal_reason': None}

def answer(query, user_groups, db_path='vector_db.json'):
    system = AnswerSystem(db_path)
    return system.answer(query, user_groups)

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "What is the fire rating for residential buildings?"
    groups_str = sys.argv[2] if len(sys.argv) > 2 else '["design"]'
    user_groups = json.loads(groups_str.replace("'", '"'))

    result = answer(query, user_groups)
    print(json.dumps(result, indent=2, ensure_ascii=False))
