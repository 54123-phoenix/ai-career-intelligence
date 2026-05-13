---
id: T-FE-004
status: todo
assignee: frontend_agent
type: feature
created: 2026-05-13
---

# Phase 2: 用户认证与注册登录

## 目标
实现用户注册、登录、登出功能，对接后端 `/auth/*` 和 `/users/me`。

## 输入
- 上游依赖：T-FE-002（API Client）、T-FE-003（状态管理）
- 参考文档：docs/frontend_architecture.md §6、§7

## 输出
- 交付文件：
  - `frontend/app/(marketing)/login/page.tsx`
  - `frontend/app/(marketing)/register/page.tsx`
  - `frontend/components/auth/LoginForm.tsx`
  - `frontend/components/auth/RegisterForm.tsx`
  - `frontend/lib/api/user.ts`（更新：实现 login/register/getMe）
  - `frontend/stores/authStore.ts`（更新：实现 login/logout 动作）
- 接口签名：
  - `loginUser(email, password) => { token, user }`
  - `registerUser(email, password, name) => { token, user }`
  - `getCurrentUser() => UserProfile`

## 约束
- 表单校验使用 Zod
- JWT token 存储于 localStorage（或 httpOnly cookie，视后端支持）
- 登录成功后跳转 /dashboard
- 注册成功后自动登录
- 后端接口若未就绪，使用 mock 数据过渡

## 验收标准
- [ ] 登录表单可提交并获取 token
- [ ] 注册表单可提交并创建用户
- [ ] 登录后 Navbar 显示用户名称
- [ ] 登出后清除 token 并跳转 /login
- [ ] 未认证用户无法访问 (app) 路由组
- [ ] `npm run build` 无错误
