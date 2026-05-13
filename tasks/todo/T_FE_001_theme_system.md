---
id: T-FE-001
status: todo
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 1: 主题系统与 Dark Mode 支持

## 目标
安装并配置 `next-themes`，实现全站 light/dark 主题切换，默认浅色，不重写现有组件，仅通过 Tailwind `dark:` 前缀扩展。

## 输入
- 上游依赖：无
- 参考文档：docs/frontend_architecture.md §5

## 输出
- 交付文件：
  - `frontend/app/layout.tsx`（更新：引入 ThemeProvider）
  - `frontend/components/ui/ThemeToggle.tsx`
  - `frontend/tailwind.config.ts`（更新：darkMode: 'class'）
  - `frontend/app/globals.css`（更新：颜色变量）
- 功能演示：Navbar 出现主题切换按钮，切换后 Dashboard/Analysis 等页面正确响应

## 约束
- 仅增加 `next-themes` 一个依赖
- Dashboard 现有深色代码迁移为 `dark:` 条件样式，不删除原有样式
- 默认主题为 light
- 主题偏好持久化（localStorage）

## 验收标准
- [ ] `npm install next-themes` 成功
- [ ] Tailwind 配置启用 `darkMode: 'class'`
- [ ] 根 layout 包裹 ThemeProvider
- [ ] Navbar 或 Settings 页面可切换主题
- [ ] Dashboard 页面在 dark 模式下保持原有深色外观
- [ ] Analysis/Simulation/Chat/Profile 在 light 模式下正常显示
- [ ] `npm run build` 无类型/样式错误
