# Take-Home Challenge (AI Allowed)
## Enterprise AI Document Search — 1-Day MVP

### Context
You are asked to build a **minimal, production-minded AI document search prototype** for an enterprise internal knowledge system.

The system is intended to support searching across internal documents such as:
- project documentation
- communication records (e.g. meeting notes, summaries)
- technical references or guidelines

This challenge focuses on **correct system design, governance, and traceability**, rather than UI or scale.

---

## Time Expectation
- ✅ **AI-assisted / “vibe coding” is allowed** (e.g. Cursor, Claude Code, Copilot).
- ✅ Expected effort: **within 1 working day**.
- ✅ We value **correctness, explainability, and engineering trade-offs** over polish.

---

## Goal
Build a minimal AI-powered document search system that includes:

1. Document ingestion and structured storage
2. Indexing and retrieval (vector search minimum)
3. A complete `answer(query, user)` pipeline with access control, expiry, citations, and refusal
4. A small, reproducible offline evaluation

You may use any language, framework, or libraries you are comfortable with.

---

## Requirements

### A) Ingestion & Data Modeling
Ingest documents from a local folder.
Minimum supported format: **`.txt` or `.md`** (PDF/Word support is optional).

Documents must be represented using two logical entities:

#### Asset (document-level)
Must include:
- `asset_id`
- `source_path`
- `doc_type`
- `version`
- `updated_at`
- `acl_groups`
- `expiry`

#### Chunk (snippet-level)
Must include:
- `chunk_id`
- `asset_id`
- `text`
- `page`
- `section_title` **or** `section_path`

Notes:
- If you are not using PDFs, `page` may be `null` or `-1`, but must be consistent.
- Section information can be heuristic, but must be traceable.

---

### B) Indexing & Retrieval
Implement at least **one retrieval method**:
- ✅ Vector retrieval (embeddings + top-K)
- (Optional bonus) Keyword or hybrid retrieval

Your retrieval layer must support **metadata filtering**:
- Access control via `acl_groups`
- Expiry filtering via `expiry`

---

### C) Core API: `answer(query, user)`

Implement a high-level function such as:

```
answer(query, user) -> {
  answer,
  citations[],
  refusal_reason?
}
```

The pipeline must form a **complete, enforceable loop**:

1. Access control and expiry enforcement
   - Must take effect **before or during retrieval**
   - Unauthorized or expired content must not enter the model context

2. Retrieval (vector / keyword / hybrid)

3. Optional reranking
   - If not used, clearly explain why (latency, cost, simplicity, etc.)

4. Evidence-based output
   - Return citations with document, page, and section information

5. Refusal handling
   - If evidence is insufficient, unauthorized, or expired, the system must refuse with a clear reason

---

### D) Minimal Offline Evaluation
Provide a small, reproducible evaluation script (`eval.py` or notebook).

You only need **one** metric, for example:
- Recall@K
- Citation accuracy
- Refusal accuracy

Include a short explanation of:
- what is measured
- what the result indicates
- limitations of the evaluation

---

## Deliverables

Please submit a **GitHub repository** (public or private).

The repository must contain:

1. `README.md`
   - how to run ingestion
   - how to run a query demo
   - how to run evaluation

2. `schema.md` (or JSON / SQL)
   - definitions of Asset and Chunk

3. Source code
   - ingestion, indexing, retrieval
   - `answer(query, user)` implementation

4. `eval.py` and a short evaluation summary

5. `design_notes.md` (about one page)
   - key design decisions and trade-offs
   - what AI assistance was used for
   - what you manually verified or adjusted

### Expected Repository Structure (Example)

This is an **example structure only**. You do **not** need to follow it exactly, but your repository should be logically organized and easy to review.

```
repo/
├── README.md
├── schema.md
├── design_notes.md
├── eval.py
├── answer.py
├── ingestion/
│   └── ingest.py
├── retrieval/
│   └── search.py
├── dataset/
│   ├── assets.csv
│   ├── queries.jsonl
│   └── docs/
│       ├── *.txt
│       └── *.md
└── requirements.txt
```

The key expectation is **clarity and traceability**, not a specific framework or layout.

---

## ✅ Verification Criteria

We will focus on the following **four verification standards**:

1. **Access control and expiry are enforced at retrieval time**
   - not only described in prompts
   - unauthorized or expired content must never be passed to the model

2. **Refusal is explicit and typed**
   Your system must distinguish at least:
   - `no_access`
   - `expired`
   - `no_evidence`

3. **Citations are verifiable**
   - citations must map to real assets and chunks
   - references must not be hallucinated

4. **Evaluation is reproducible and interpretable**
   - evaluators can re-run it and see the same results
   - you can explain what the metric proves (and what it does not)

---

## What Is Not Required
- No frontend UI
- No cloud deployment
- No large-scale infrastructure
- No multi-agent orchestration

Focus on **correctness, governance, traceability, and reasoning quality**.
