# Enterprise AI Document Search

A minimal RAG system for enterprise document search with access control and citation tracking.

## Setup

```bash
pip install -r requirements.txt
```

## Ingestion

```bash
python -m ingestion.ingest take_home_dataset/docs take_home_dataset/assets.csv
```

This creates `vector_db.json` with embedded documents.

## Query Demo

```bash
python answer.py "What is the fire rating for residential buildings?" '["design"]'
```

## Evaluation

```bash
python eval.py
```

## Architecture

- `ingestion/ingest.py` - Document ingestion and chunking
- `retrieval/search.py` - Vector search with metadata filtering
- `answer.py` - Answer pipeline with access control and citations
- `eval.py` - Refusal accuracy evaluation
