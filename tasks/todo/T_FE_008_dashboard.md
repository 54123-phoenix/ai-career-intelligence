---
id: T-FE-008
status: todo
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 6: 仪表盘整合与旧代码清理

## 目标
重构 /dashboard 页面为业务概览中心，移除所有 pipeline/Agent 暴露，并标记旧代码 deprecated。

## 输入
- 上游依赖：T-FE-005（Analysis）、T-FE-006（Simulation）、T-FE-007（Chat/Profile）
- 参考文档：docs/frontend_architecture.md §8
- 现有代码：`frontend/app/dashboard/page.tsx`（需大幅重构）

## 输出
- 交付文件：
  - `frontend/app/dashboard/page.tsx`（重构）
  - `frontend/components/dashboard/StatsGrid.tsx`
  - `frontend/components/dashboard/TaskProgress.tsx`
  - `frontend/components/dashboard/RecentActivity.tsx`
  - `frontend/components/dashboard/RecommendationCarousel.tsx`
  - 旧文件标记 deprecated：
    - `frontend/lib/t008-api.ts`（加 @deprecated 注释）
    - `frontend/lib/t009-api.ts`（加 @deprecated 注释）
    - `frontend/lib/t010-api.ts`（加 @deprecated 注释）
    - `frontend/types/t008.ts`（加 @deprecated 注释）
    - `frontend/types/t009.ts`（加 @deprecated 注释）
    - `frontend/types/t010.ts`（加 @deprecated 注释）

## 约束
- Dashboard 不再展示 execution_id、pipeline version、T010 Lightweight Core
- 状态栏改为展示业务指标：推荐岗位数、进行中任务、技能完成度
- 旧文件保留，仅加注释标记，不删除
- 验证所有旧路由重定向生效

## 验收标准
- [ ] Dashboard 无 pipeline/Agent 暴露
- [ ] 展示用户概览、推荐职业、任务进度
- [ ] 旧 API/类型文件已标记 @deprecated
- [ ] 旧路由重定向验证通过
- [ ] `npm run build` 零错误
- [ ] `npm run lint` 零警告
