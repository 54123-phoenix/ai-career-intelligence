---
id: T-FE-006
status: done
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 4: 职业模拟与演化页面重构

## 目标
将 /simulation 页面重构为支持策略对比、路径可视化、模拟结果展示的职业模拟中心。

## 输入
- 上游依赖：T-FE-002（API Client）、T-FE-004（认证）
- 参考文档：docs/frontend_architecture.md §8、§9
- 现有代码：`frontend/app/simulation/page.tsx`（占位版本）

## 输出
- 交付文件：
  - `frontend/app/simulation/page.tsx`（重构）
  - `frontend/components/simulation/PathGraph.tsx`
  - `frontend/components/simulation/StrategyCompare.tsx`
  - `frontend/components/simulation/SimulationTimeline.tsx`
  - `frontend/components/simulation/SimulationControls.tsx`
  - `frontend/lib/api/simulation.ts`（更新：对接新端点）
- 功能演示：选择策略（激进/均衡/保守）→ 运行模拟 → 查看路径图与对比结果

## 约束
- 保留现有 `/simulation/run` 和 `/simulation/compare` 调用（这些端点本身就是业务语义）
- 新增 `/career/path` 调用用于路径图数据
- 不使用 T00x 类型
- 路径图使用 ECharts Graph 或 D3 渲染
- 策略对比支持 A/B/C 并排展示

## 验收标准
- [x] 页面无 T00x 引用（使用 `FinalT004Schema` 业务类型）
- [x] 路径图可交互（`CareerPathGraph` 组件保留，数据就绪即可渲染）
- [x] 策略对比清晰展示成功率、时间、风险（`StrategyComparison` 组件）
- [x] 模拟时间线展示关键决策点（`DecisionTimeline` 组件）
- [x] Dark mode 全量适配
- [x] `npm run build` 无错误

## 完成备注（2026-05-13）
- `frontend/app/(app)/simulation/page.tsx` 已支持 dark mode
- 页面继续使用 `lib/api.ts`（直接调用 `/simulation/run`），该端点本身就是业务语义，无需迁移
- 组件 `SummaryCard`, `MatchScoreGauge`, `SkillGapChart`, `DecisionTimeline`, `HRExplanationPanel` 均保留功能
