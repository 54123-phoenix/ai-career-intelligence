---
id: T-FE-005
status: todo
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 3: 职业分析引擎页面重构

## 目标
将 /analysis 页面重构为完整的职业分析引擎：简历上传 → 解析 → 岗位推荐 → 匹配评分 → 策略生成 → 可视化。

## 输入
- 上游依赖：T-FE-002（API Client）、T-FE-004（认证）
- 参考文档：docs/frontend_architecture.md §8、§9
- 现有代码：`frontend/app/analysis/page.tsx`（占位版本）

## 输出
- 交付文件：
  - `frontend/app/analysis/page.tsx`（重构）
  - `frontend/components/analysis/ResumeUploader.tsx`
  - `frontend/components/analysis/SkillRadar.tsx`
  - `frontend/components/analysis/JobMatchCard.tsx`
  - `frontend/components/analysis/MatchScoreBadge.tsx`
  - `frontend/components/analysis/StrategyPanel.tsx`
  - `frontend/components/analysis/CareerPlanTimeline.tsx`
  - `frontend/lib/api/career.ts`（更新：对接新端点）
- 功能演示：用户输入职业目标 → 点击分析 → 看到技能雷达图、推荐岗位列表、策略对比、职业规划时间线

## 约束
- 不使用 T00x 类型，全部使用 `types/career.ts`
- 不使用 `lib/t008-api.ts`、`lib/t009-api.ts`、`lib/t010-api.ts`
- Loading 状态展示业务阶段（"正在解析画像..."），不展示 Agent 名称
- 策略建议用弹窗/面板形式展示（AI建议弹窗）
- 对接后端 `/career/analyze`（若未就绪，先 mock）

## 验收标准
- [ ] 页面无 T00x 引用
- [ ] 技能雷达图使用 ECharts 渲染
- [ ] 岗位推荐卡片展示匹配度评分
- [ ] 策略面板展示多维度评分与风险提示
- [ ] 职业规划时间线可交互
- [ ] `npm run build` 无错误
