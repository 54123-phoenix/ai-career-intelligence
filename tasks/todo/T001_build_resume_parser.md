---
id: T-001
status: done
assignee: parser_agent
type: feature
created: 2025-01-15
completed: 2025-01-15
reviewer: pending (@reviewer_agent)
---

# 实现 Resume Parser 核心模块

## 目标
实现 `backend/parser/resume_parser.py`，支持 PDF / Markdown / 纯文本简历解析，输出 `StructuredResume` Pydantic 模型。

## 输出
- [x] `backend/parser/resume_parser.py` — LLM 解析 + 规则回退 + Pydantic 校验
- [x] `backend/parser/pdf_extractor.py` — pymupdf 文本提取
- [x] `backend/parser/schemas.py` — 技能同义词映射 (50+ entries) + LLM prompt 模板
- [x] `backend/parser/exceptions.py` — ParseError / PDFExtractionError / SchemaValidationError
- [x] `data/test_resumes/sample_markdown.md` — 中文简历样本
- [x] `data/test_resumes/sample_text.txt` — 英文简历样本
- [x] `tests/test_parser.py` — 技能标准化 / PDF 异常 / 规则回退 / 模型校验 4 组测试

## 验收
- [x] 支持 PDF (pymupdf) / Markdown / 纯文本三种输入
- [x] LLM 输出 schema 校验失败 → 自动回退 regex 规则解析
- [x] 技能标准化映射表覆盖 50+ 常见变体
- [ ] 待 @reviewer_agent 审查
