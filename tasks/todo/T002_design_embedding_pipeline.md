---
id: T-002
status: done
assignee: retrieval_agent
type: feature
created: 2025-01-15
completed: 2025-01-15
dependencies: T-001 (StructuredResume schema)
reviewer: pending (@reviewer_agent)
---

# 设计 Embedding Pipeline 与 Qdrant Collection

## 目标
实现 `backend/retrieval/` 模块，包含 embedding 生成、Qdrant 向量存储、语义检索。

## 输出
- [x] `backend/retrieval/schemas.py` — collection configs, text flattening (resume_to_text / job_to_text)
- [x] `backend/retrieval/embedder.py` — Embedder class (sentence-transformers, 384 dim, lazy load, batch encode)
- [x] `backend/retrieval/qdrant_client.py` — QdrantStore (in-memory MVP, upsert, cosine search)
- [x] `backend/retrieval/retriever.py` — Retriever (index_resume, index_job, search_jobs, search_resumes)
- [x] `backend/retrieval/__init__.py` — public API exports
- [x] `tests/test_retrieval.py` — 5 test classes: text flattening, MatchResult, QdrantStore, Embedder, Retriever

## 架构
```
Retriever (orchestration)
  ├── Embedder (sentence-transformers, 384 dim, lazy load)
  └── QdrantStore (in-memory, cosine similarity)
```

## 验收
- [x] Embedding model: all-MiniLM-L6-v2, 384 dim, normalize_embeddings=True
- [x] 3 collections: resumes / jobs
- [x] search_jobs() 返回 list[MatchResult]
- [x] 支持预计算 embedding (skill_embedding / job_embedding)
- [x] 批量索引: upsert_batch
- [x] 反向查询: search_resumes
- [x] Qdrant in-memory MVP (可切换 local/remote)
- [ ] 待 @reviewer_agent 审查
