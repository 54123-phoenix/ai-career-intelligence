---
id: T-000
status: doing
assignee: architect_agent
type: setup
created: 2025-01-15
started: 2025-01-15
---

# 项目骨架与多 Agent 开发框架搭建

## 目标
搭建 AI Career Intelligence 项目的多 Agent 协作开发框架，包括目录结构、核心文档、共享类型和任务看板。

## 输入
- 用户需求：多 Agent 职业智能决策系统
- 参考：CLAUDE.md 设计规范

## 输出
- [x] `CLAUDE.md` —— AI Team Operating System
- [x] `agents/*.md` —— 6 个专业 Agent Prompt
- [x] `docs/architecture.md` —— 系统架构
- [x] `docs/api_contracts.md` —— API 契约 v1.0.0
- [x] `docs/system_flow.md` —— 数据流与状态机
- [x] `backend/shared/types.py` —— 共享 Pydantic 模型
- [x] `tasks/todo/` —— 初始任务队列（T-001 ~ T-003）
- [ ] `backend/api/contracts/` —— HTTP 接口契约（待补充）

## 约束
- 所有 Agent 目录边界明确
- 共享类型必须被所有模块引用
- 任务系统必须可运转

## 当前状态
框架搭建完成，等待 @reviewer_agent 审查后进入 done。
