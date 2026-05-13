---
id: T-FE-004
status: done
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
- [x] 登录表单可提交并获取 token（对接 `/auth/login`）
- [x] 注册表单可提交并创建用户（对接 `/auth/register`）
- [x] 登录后 Navbar 显示用户名称/头像下拉菜单
- [x] 登出后清除 token 并跳转 /login
- [x] 未认证用户无法访问 (app) 路由组（`(app)/layout.tsx` AuthGuard）
- [x] `npm run build` 无错误

## 完成备注（2026-05-13）
- `frontend/app/(marketing)/login/page.tsx` 与 `register/page.tsx` 已对接真实后端 API
- `frontend/stores/authStore.ts` 管理登录态，持久化 token，支持 `fetchUser` 恢复会话
- `frontend/components/layout/Navbar.tsx` 新增用户头像下拉菜单（用户中心链接 + 退出登录）
- 后端 `backend/api/routes/auth.py` 已修复 Bearer Header 认证提取
