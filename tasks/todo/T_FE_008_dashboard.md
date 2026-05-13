---
id: T-FE-008
status: in_progress
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
- [ ] Dashboard 无 pipeline/Agent 暴露（旧代码仍在，已标记 @deprecated）
- [ ] 展示用户概览、推荐职业、任务进度（待重构）
- [x] 旧 API/类型文件已标记 @deprecated（`lib/career-api.ts` 已标记，未使用旧文件已清理）
- [x] 旧路由重定向验证通过（`/career/growth` → `/analysis` 等）
- [x] `npm run build` 零错误（12 路由全部通过）
- [ ] `npm run lint` 零警告（未执行）

## 进展备注（2026-05-13）
- `frontend/app/(app)/dashboard/page.tsx` 仍保留旧 T010 代码（332 行），已添加文件级 `@deprecated` 注释。
- 清理工作已完成：删除 `lib/t008-api.ts`、恢复 `lib/mock-data.ts`（t010 fallback 仍需）。
- Landing 页面已创建（`(marketing)/page.tsx`），根路由 `/` 不再重定向到 `/dashboard`。
- Settings 页面已创建（`(app)/settings/page.tsx`），提供主题切换与数据清除功能。
- Navbar 已升级为包含用户头像下拉菜单。

## 剩余工作
- Dashboard 全面重写：移除 `ActOneInput`/`ActTwoStrategy`/`ActThreeSimulation` 等旧组件引用，替换为 `StatsGrid` + `RecentActivity` + 快捷入口的业务概览布局。
