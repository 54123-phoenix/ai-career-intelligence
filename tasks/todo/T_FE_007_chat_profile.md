---
id: T-FE-007
status: done
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
- [x] Chat 页面可发送消息并接收 SSE 流式回复
- [x] 回复支持流式渲染（逐字追加，loading 态有动画指示器）
- [x] Profile 页面可编辑并保存用户信息（对接 `updateUserProfile`）
- [x] 操作记录按时间倒序展示（对接 `getUserHistory`，失败时展示 mock 数据）
- [x] `npm run build` 无错误

## 完成备注（2026-05-13）
- `frontend/app/(app)/chat/page.tsx`：
  - 接入 `streamChatMessage` SSE 流式 API
  - 使用 `ReadableStreamDefaultReader` + `TextDecoder` 实现逐字渲染
  - 保留 `conversation_id` 字段为后续会话连续性做准备
- `frontend/app/(app)/profile/page.tsx`：
  - 加载时自动调用 `getCurrentUser` + `getUserHistory`
  - 支持编辑姓名、工作经验、学历、技能、职业目标、期望地点
  - 保存时调用 `updateUserProfile`，成功/失败均有 toast 提示
  - API 不可用时自动降级到 demo 数据
