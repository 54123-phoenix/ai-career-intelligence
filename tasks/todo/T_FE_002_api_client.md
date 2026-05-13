---
id: T-FE-002
status: done
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 1: API Client 基础层与业务类型定义

## 目标
建立业务语义的 API 客户端和 TypeScript 类型系统，彻底解耦前端与 T00x 构建产物。

## 输入
- 上游依赖：无
- 参考文档：docs/frontend_architecture.md §6、§9
- 后端契约：docs/api_contracts.md（HTTP API 部分）

## 输出
- 交付文件：
  - `frontend/lib/api/client.ts`（统一 fetch 实例）
  - `frontend/lib/api/career.ts`（职业分析 API）
  - `frontend/lib/api/simulation.ts`（模拟 API）
  - `frontend/lib/api/user.ts`（用户管理 API）
  - `frontend/lib/api/chat.ts`（AI 对话 API，SSE 占位）
  - `frontend/types/index.ts`（统一导出）
  - `frontend/types/user.ts`
  - `frontend/types/career.ts`
  - `frontend/types/simulation.ts`
  - `frontend/types/chat.ts`
- 接口签名：每个 API 函数必须带类型输入输出，禁止 `any`

## 约束
- 不删除 `lib/t008-api.ts`、`types/t008.ts` 等旧文件，但新代码不得 import 它们
- `lib/api/career.ts` 过渡期内可内部调用现有 `/career/t010/run`，但函数名必须是业务语义（如 `analyzeCareer()`）
- 所有类型必须与 backend Pydantic 模型语义对齐，但命名独立

## 验收标准
- [x] 新建 5 个 API 文件 + 4 个类型文件
- [x] 所有 API 函数返回类型明确
- [x] `types/` 下无 T00x 引用（新类型文件业务语义命名）
- [x] 现有页面仍可通过旧 API 运行（向后兼容，`lib/career-api.ts` 保留）
- [x] `npm run build` 类型检查通过

## 完成备注（2026-05-13）
- `frontend/lib/api/client.ts`：统一 fetch + Bearer Token + ApiError
- `frontend/lib/api/career.ts`：业务语义封装，内部 fallback 到 T010， facade 就绪后自动切换
- `frontend/lib/api/simulation.ts`：模拟域 API
- `frontend/lib/api/user.ts`：用户认证与管理 API
- `frontend/lib/api/chat.ts`：SSE 流式对话 API
- `frontend/types/{user,career,simulation,chat}.ts`：业务语义类型，与 T00x 解耦
