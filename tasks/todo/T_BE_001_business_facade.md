---
id: T-BE-001
status: in_progress
assignee: architect_agent
type: feature
created: 2026-05-13
---

# 后端：新建业务 Facade API

## 目标
将后端 T008/T009/T010 构建管道端点收敛为业务语义 facade，对外隐藏实现细节，旧端点保留并标记 deprecated。

## 输入
- 上游依赖：无
- 参考文档：docs/frontend_architecture.md §6、docs/api_contracts.md
- 现有代码：`backend/api/routes/career.py`、`backend/career/t008_pipeline.py`、t009、t010

## 输出
- 交付文件：
  - `backend/services/career_service.py`（统一服务层）
  - `backend/api/routes/v1/career.py`（新业务路由，或更新现有 career.py）
  - 新增端点：
    - `POST /career/analyze`
    - `POST /career/resume`
    - `GET /career/recommendations`
    - `GET /career/match-score`
    - `POST /career/feedback`
    - `GET /career/path`
    - `GET /career/trends`
  - 新增端点：
    - `POST /auth/register`
    - `POST /auth/login`
    - `GET /users/me`
    - `PATCH /users/me`
    - `GET /users/me/history`
  - 新增端点：
    - `POST /chat/message`（SSE）✅ 已创建 `backend/api/routes/chat.py`
- 旧端点标记 deprecated：在 `/career/t008/*`、`/career/t009/*`、`/career/t010/*` 的响应头加 `Deprecation: true`

## 约束
- 内部可复用现有 T009/T010 pipeline 逻辑
- 对外响应类型必须与 docs/api_contracts.md 中定义的业务模型对齐
- Pydantic 模型复用 `backend/career/schemas.py`，不新建 T00x 模型
- 认证使用 JWT，middleware 注入当前用户

## 验收标准
- [x] 新 facade 端点可通过 Postman/curl 调用（`/career/analyze`, `/auth/register`, `/auth/login`, `/users/me`, `/users/me/history` 已就绪）
- [x] 旧 T008/T009/T010 端点仍可访问（向后兼容）
- [x] 旧端点响应包含 deprecation 标记（main.py 中 `deprecation_middleware` 为所有 `/career/t008/*`、`/career/t009/*`、`/career/t010/*` 响应注入 `Deprecation: true` 和 `Sunset: 2026-12-31`）
- [x] 新端点类型与前端 `types/*.ts` 对齐（前端 `adaptApiToCareerResult` 已适配字段映射）
- [ ] 单元测试覆盖新 facade 逻辑

## 进展备注（2026-05-13）
- `backend/api/routes/auth.py`：Bearer Token Header 认证已修复，注册/登录/获取用户/更新用户/历史记录均可用。
- `backend/api/routes/career.py`：Facade 端点已存在（`/career/analyze`, `/career/resume`, `/career/recommendations`, `/career/match-score`, `/career/feedback`, `/career/path`, `/career/trends`），但 `analyze` 外的端点多为占位符/MVP。
- 旧端点 deprecation header：文件末尾有 placeholder wrapper，但未真正通过 middleware 注入。
