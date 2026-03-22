# Design Notes

## Key Decisions

### Vector Search over Keyword Search
Simple cosine similarity on BGE-M3 embeddings provides semantic matching suitable for natural language queries. No BM25 hybrid needed for this small dataset.

### No Reranking
Reranking adds latency without significant benefit for top-5 retrieval on a small corpus. Simple vector search is sufficient.

### Access Control Enforcement
Access control is enforced at retrieval time by filtering chunks before they enter the context. Expired documents are filtered using current date comparison against the expiry field.

### Refusal Typing
System returns typed refusal reasons: `no_access`, `expired`, `no_evidence`. This enables precise evaluation and user feedback.

## AI Assistance
Used AI to generate code structure and boilerplate. Manually verified:
- Access control logic correctness
- Citation format accuracy
- Evaluation metric interpretation
