# Schema Definitions for Enterprise AI Document Search

## Asset (Document-Level Entity)

| Field | Type | Description |
|-------|------|-------------|
| asset_id | string | Unique identifier for the document |
| source_path | string | Relative path to the source file |
| doc_type | string | Type: project, meeting, guideline |
| version | integer | Document version number |
| updated_at | string | ISO date of last update |
| acl_groups | list[string] | Groups with access: design, pm, all |
| expiry | string | ISO date when document expires |

## Chunk (Snippet-Level Entity)

| Field | Type | Description |
|-------|------|-------------|
| chunk_id | string | Unique identifier for the chunk |
| asset_id | string | Reference to parent Asset |
| text | string | Content text of the chunk |
| page | integer | Page number (-1 for non-PDF) |
| section_title | string | Heuristic section title |
| section_path | string | Hierarchical path to section |
