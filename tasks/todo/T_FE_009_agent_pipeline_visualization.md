---
id: T-FE-009
status: todo
assignee: unassigned
type: feature
created: 2026-05-13
---

# Agent Pipeline 可视化 — 分析执行链路图

## 目标
在职业分析过程中，前端实时展示多 Agent 协作的 Pipeline 执行链路图，让评委/用户直观看到「解析→检索→评审→架构→模拟」各阶段的状态流转，体现项目核心 AI 竞争力。

## 输入
- 上游依赖：T-FE-005（职业分析引擎页面）
- 参考文档：CLAUDE.md §5（专业 Agent 列表）、docs/architecture.md
- 后端接口：分析执行时返回的 `execution_trace` 或流式 `step_events`（若后端尚未支持，需先与 backend_agent 协商契约）
- 现有代码：`frontend/app/(app)/analysis/page.tsx`、`frontend/components/analysis/SkillRadar.tsx`

## 输出
- 交付文件：
  - `frontend/components/analysis/PipelineVisualizer.tsx`（核心执行链路组件）
  - `frontend/components/analysis/AgentStepNode.tsx`（单步骤节点）
  - `frontend/components/analysis/AgentTraceLog.tsx`（详细日志面板）
  - `frontend/types/trace.ts`（执行链路类型定义）
  - 更新 `frontend/app/(app)/analysis/page.tsx`（在分析 loading 阶段展示 Pipeline）
- 功能演示：用户点击「开始职业分析」→ 页面中央/顶部出现横向/纵向 Pipeline 流程图 → 各 Agent 节点依次高亮（解析中→检索中→评审中...）→ 最终节点显示 ✅/❌ 状态

## 约束
- **大赛核心加分项**：此功能直接体现「多 Agent 协同」不是口号，而是可视化的技术实现
- 不使用 T00x 类型，全部使用业务语义类型
- 视觉风格需与现有 Dark Mode / Glass Card 设计系统一致（参考 `globals.css` 的 neon/glass 变量）
- 支持两种展示模式：
  1. **极简模式**：6 个节点横向流程条（适合分析页顶部 inline 展示）
  2. **详情模式**：带日志输出、耗时、置信度的展开面板（适合点击展开）
- 若后端 trace 数据未就绪，前端先使用基于 `depth`（quick/standard/deep）的预设步骤 mock，接口就绪后无缝切换真实数据
- 动画要求：节点激活时要有 pulse-glow 动效；节点间连线要有流动效果（CSS animation 或 SVG stroke-dashoffset）

## 验收标准
- [ ] Pipeline 流程图在 analysis 页面分析过程中可见
- [ ] 至少展示 5 个核心 Agent 节点：Parser → Retrieval → Reviewer → Architect → Simulation
- [ ] 每个节点有状态：waiting / running / success / failed
- [ ] 有整体执行进度百分比
- [ ] `npm run build` 无错误
- [ ] 类型完备，无 `any`
- [ ] 支持 Dark Mode 与 Light Mode 自动适配

## 备注
- 本任务**暂不动工**，待项目其他高优先级任务（性能、类型、基础功能）完成后，由 frontend_agent 认领执行。
- 此功能是阿里云智聘创新AI+大赛评审关注点之一，建议在提交前 3-5 天完成。
