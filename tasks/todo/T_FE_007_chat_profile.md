---
id: T-FE-007
status: todo
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 5: AI 助手对话与用户中心

## 目标
实现 /chat 页面的 SSE 流式对话，以及 /profile 页面的用户信息管理与操作记录。

## 输入
- 上游依赖：T-FE-002（API Client）、T-FE-004（认证）
- 参考文档：docs/frontend_architecture.md §8、§9

## 输出
- 交付文件：
  - `frontend/app/chat/page.tsx`（重构：SSE 流式）
  - `frontend/components/chat/ChatWindow.tsx`
  - `frontend/components/chat/ChatInput.tsx`
  - `frontend/components/chat/SuggestionChips.tsx`
  - `frontend/components/chat/StreamingMessage.tsx`
  - `frontend/app/profile/page.tsx`（重构）
  - `frontend/lib/api/chat.ts`（更新：SSE 实现）
  - `frontend/lib/api/user.ts`（更新：history 接口）
- 功能演示：
  - Chat：输入问题 → 流式接收 AI 回复 → 支持 Markdown
  - Profile：编辑信息 → 查看历史操作记录

## 约束
- Chat SSE 使用 `EventSource` 或 `fetch` + `ReadableStream`
- 消息历史缓存在 Zustand store 中
- 操作记录从 `/users/me/history` 获取，支持分页
- 后端接口若未就绪，使用 mock 过渡

## 验收标准
- [ ] Chat 页面可发送消息并接收回复
- [ ] 回复支持流式渲染（打字机效果）
- [ ] Profile 页面可编辑并保存用户信息
- [ ] 操作记录按时间倒序展示
- [ ] `npm run build` 无错误
