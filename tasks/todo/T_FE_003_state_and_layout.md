---
id: T-FE-003
status: todo
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 1: Zustand 状态管理与应用布局

## 目标
建立 Zustand 全局状态管理，重构根布局为 `(marketing)` 和 `(app)` 路由组，提供统一的 AppShell。

## 输入
- 上游依赖：T-FE-001（主题系统）、T-FE-002（API Client）
- 参考文档：docs/frontend_architecture.md §7、§4

## 输出
- 交付文件：
  - `frontend/stores/authStore.ts`
  - `frontend/stores/careerStore.ts`
  - `frontend/stores/uiStore.ts`
  - `frontend/components/layout/AppShell.tsx`
  - `frontend/components/layout/Sidebar.tsx`
  - `frontend/components/layout/MobileNav.tsx`
  - `frontend/app/(marketing)/layout.tsx`
  - `frontend/app/(app)/layout.tsx`
  - `frontend/app/(marketing)/page.tsx`（Landing 页占位）
- 功能演示：登录后进入 (app) 路由组，看到 Navbar + Sidebar；未登录访问 /dashboard 重定向到 /login

## 约束
- Zustand store 不用于 Server Components
- AuthGuard 通过 Client Component 高阶组件或 middleware 实现
- AppShell 在移动端自动切换为底部导航
- 不引入额外状态管理库

## 验收标准
- [ ] Zustand 3 个 store 可独立运行
- [ ] (marketing) 和 (app) 路由组分离
- [ ] 未登录访问 /dashboard 重定向到 /login
- [ ] Navbar 在所有 (app) 页面一致出现
- [ ] Sidebar 在桌面端可见，移动端隐藏
- [ ] `npm run build` 无错误
