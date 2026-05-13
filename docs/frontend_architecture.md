# 前端架构设计文档 v2.0

> 版本: 2.0.0
> 日期: 2026-05-13
> 维护者: Orchestrator / Frontend Agent
> 约束: 本文档取代 agents/frontend_agent.md 中过时的页面路由与组件结构定义

---

## 1. 设计目标

将前端从"暴露构建任务编号（T008/T009/T010）与开发 Agent 名称"的混乱状态，重构为**以用户业务旅程为中心**的现代 Next.js 14 应用。

核心原则：
- **用户无感构建历史**：前端代码、路由、文案、类型中不得出现 T00x 编号或构建 Agent 名称
- **业务语义 API**：前端只调用业务 facade 接口，不直接调用 T008/T009/T010 端点
- **主题可控**：支持 light/dark 切换，默认浅色，不增加过量工程负担
- **向后兼容**：旧路由、旧端点保留但标记 deprecated，前端内部逻辑完全走新链路

---

## 2. 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Framework | Next.js | 14+ (App Router) | Server Components 优先获取初始数据 |
| Language | TypeScript | 5.7+ | strict mode |
| Styling | Tailwind CSS | 3.4+ | + `next-themes` 支持 dark mode |
| UI Components | shadcn/ui | — | 原子组件库，统一设计系统 |
| State | Zustand | 4.x | 轻量全局状态，跨 Server/Client 边界友好 |
| Data Fetch | Server Actions + fetch | — | Server Components 读，Client Components 交互 |
| Charts | ECharts / Recharts | — | 技能雷达图、路径图、热力图 |
| Icons | lucide-react | — | 统一图标体系 |
| Forms | React Hook Form + Zod | — | 用户表单校验 |

---

## 3. 目录结构

```
frontend/
├── app/
│   ├── (marketing)/
│   │   ├── page.tsx
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (app)/
│   │   ├── layout.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── analysis/page.tsx
│   │   ├── simulation/page.tsx
│   │   ├── chat/page.tsx
│   │   ├── profile/page.tsx
│   │   └── settings/page.tsx
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/
│   ├── layout/
│   ├── auth/
│   ├── analysis/
│   ├── simulation/
│   ├── dashboard/
│   └── chat/
├── lib/
│   ├── api/
│   ├── hooks/
│   └── utils.ts
├── stores/
├── types/
└── public/
```

详见各目录说明（第 7 节）。

---

## 4. 路由设计

| 路由 | 路由组 | 访问控制 | 功能模块 |
|------|--------|---------|---------|
| `/` | (marketing) | 公开 | Landing 页 |
| `/login` | (marketing) | 公开 | 用户登录 |
| `/register` | (marketing) | 公开 | 用户注册 |
| `/dashboard` | (app) | 需登录 | 仪表盘/首页 |
| `/analysis` | (app) | 需登录 | 职业分析引擎 |
| `/simulation` | (app) | 需登录 | 职业模拟与演化 |
| `/chat` | (app) | 需登录 | AI 助手对话 |
| `/profile` | (app) | 需登录 | 用户中心 |
| `/settings` | (app) | 需登录 | 系统设置 |

**向后兼容重定向**（`next.config.js`）：
- `/career/growth` → `/analysis`
- `/career/growth-v2` → `/analysis`
- `/career/_growth-lite` → `/analysis`
- `/simulation/report` → `/simulation`

---

## 5. 主题系统

### 5.1 设计约束（工程量控制）

- **不引入全新设计系统**：基于现有 Tailwind 配置扩展
- **不重写所有组件**：使用 Tailwind `dark:` 前缀做条件样式
- **依赖最小化**：仅增加 `next-themes` 一个包
- **默认浅色**：减少用户认知负担，深色作为可选

### 5.2 实现方案

1. **Provider 层**：根 layout 包裹 `ThemeProvider`（来自 `next-themes`）
2. **切换器**：Navbar 或 Settings 页面提供切换按钮
3. **Tailwind 配置**：启用 `darkMode: 'class'`，通过 `html.dark` 控制
4. **组件适配策略**：
   - 新组件一律写双版本：`bg-white dark:bg-slate-950`
   - Dashboard 现有深色代码迁移为 `dark:` 条件样式
   - Analysis/Simulation/Chat/Profile 现有浅色代码作为默认

### 5.3 颜色 Token 规范

| 语义 | Light | Dark |
|------|-------|------|
| 页面背景 | `bg-white` | `bg-slate-950` |
| 卡片背景 | `bg-white` | `bg-slate-900` |
| 边框 | `border-gray-200` | `border-slate-800` |
| 主文本 | `text-gray-900` | `text-slate-100` |
| 次文本 | `text-gray-500` | `text-slate-400` |
| 主按钮 | `bg-indigo-600` | `bg-indigo-500` |
| 强调色 | `text-indigo-600` | `text-cyan-400` |

---

## 6. API 层设计

### 6.1 前端 API Client 结构

```
lib/api/
├── client.ts          # 统一 fetch 实例：baseURL、auth header、error handling
├── career.ts          # 职业分析引擎 API
├── simulation.ts      # 模拟 API
├── user.ts            # 用户管理 API
└── chat.ts            # AI 对话 API（SSE 流式）
```

### 6.2 与后端 API 映射

前端 API 文件 → 后端业务 facade 端点（**不走 T00x 端点**）：

| 前端 lib/api/*.ts | 调用端点 | 说明 |
|------------------|---------|------|
| `user.ts` | `POST /auth/register` | 注册 |
| | `POST /auth/login` | 登录 |
| | `GET /users/me` | 获取当前用户 |
| | `PATCH /users/me` | 更新用户 |
| | `GET /users/me/history` | 操作记录 |
| `career.ts` | `POST /career/analyze` | 综合分析（解析+推荐+策略）|
| | `POST /career/resume` | 上传简历 |
| | `GET /career/recommendations` | 岗位推荐列表 |
| | `GET /career/match-score` | 匹配评分 |
| | `POST /career/feedback` | 用户反馈 |
| `simulation.ts` | `POST /simulation/run` | 单策略模拟（保留）|
| | `POST /simulation/compare` | 多策略对比（保留）|
| | `GET /career/path` | 职业路径图数据 |
| `chat.ts` | `POST /chat/message` | AI 对话（SSE）|

### 6.3 向后兼容说明

- 前端**不直接 import** `lib/t008-api.ts`、`lib/t009-api.ts`、`lib/t010-api.ts`
- 上述文件保留在仓库中但标记为 `// @deprecated — 内部兼容用，前端不直接调用`
- 后端旧的 `/career/t008/*`、`/career/t009/*`、`/career/t010/*` 端点保留运行，响应头加 `Deprecation: true`
- 过渡期内，`lib/api/career.ts` 内部可临时转发到现有端点，但函数名必须是业务语义

---

## 7. 状态管理（Zustand）

### 7.1 为何选 Zustand

- Next.js 14 Server Components 不能直接使用 Context
- Zustand store 可在 Client Component 中随处 `import` 使用，不受组件层级限制
- 无需 Provider 包裹，减少 layout 复杂度
- TypeScript 支持优秀，体量小（~1KB）

### 7.2 Store 划分

```typescript
// stores/authStore.ts
interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// stores/careerStore.ts
interface CareerState {
  currentAnalysis: CareerAnalysisResult | null;
  history: CareerAnalysisResult[];
  isAnalyzing: boolean;
  runAnalysis: (input: string) => Promise<void>;
  clearAnalysis: () => void;
}

// stores/uiStore.ts
interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  toast: ToastItem | null;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}
```

---

## 8. 组件分层规范

### 8.1 分层定义

| 层级 | 目录 | 职责 | 示例 |
|------|------|------|------|
| 原子组件 | `components/ui/` | shadcn/ui 基础元素，无业务逻辑 | Button, Card, Dialog |
| 布局组件 | `components/layout/` | 页面骨架，控制导航和结构 | Navbar, Sidebar, AppShell |
| 业务组件 | `components/{domain}/` | 特定领域的可复用组件 | SkillRadar, JobMatchCard |
| 页面组件 | `app/**/page.tsx` | 组合业务组件，管理页面级状态 | analysis/page.tsx |

### 8.2 Server vs Client 边界

- **Server Components（默认）**：Landing、Dashboard 初始数据、Settings
- **Client Components（'use client'）**：含交互、表单、图表、对话的组件
- **混合模式**：页面级 Server Component 获取初始数据，内部嵌入 Client Component 处理交互

---

## 9. 类型系统

### 9.1 核心原则

- `types/` 目录下所有类型均为**业务语义命名**，与 T00x 解耦
- 不直接 import `types/t008.ts`、`types/t009.ts`、`types/t010.ts`
- 上述文件保留为历史参考，但不参与新代码编译路径

### 9.2 核心类型

```typescript
// types/career.ts
export interface CareerAnalysisResult {
  id: string;
  status: 'success' | 'partial' | 'failed';
  userProfile: UserProfileSummary;
  recommendations: JobRecommendation[];
  strategies: CareerStrategy[];
  plan?: CareerPlan;
  simulationResult?: SimulationSummary;
  generatedAt: string;
}

export interface JobRecommendation {
  id: string;
  title: string;
  company: string;
  location: string;
  matchScore: number;
  requiredSkills: string[];
  salaryRange?: [number, number];
}

export interface CareerStrategy {
  id: string;
  name: string;
  description: string;
  overallScore: number;
  dimensions: Record<string, number>;
  isOffPath: boolean;
}

// types/user.ts
export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'user' | 'admin';
  experienceYears: number;
  educationLevel: string;
  skills: string[];
  careerGoals: string[];
  preferredLocations: string[];
}

// types/simulation.ts
export interface SimulationResult {
  id: string;
  strategyName: string;
  outcome: 'accepted' | 'rejected' | 'timeout';
  successProbability: number;
  timeline: SimulationEvent[];
  skillGap: SkillGapItem[];
  recommendations: string[];
}

// types/chat.ts
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}
```

---

## 10. 重构路线图

### Phase 1: 基础设施（1-2 天）
- [ ] 安装 `next-themes`，配置 Tailwind dark mode
- [ ] 新建 `lib/api/{client,career,simulation,user,chat}.ts`
- [ ] 新建 `types/{user,career,simulation,chat}.ts`
- [ ] 新建 `stores/{auth,career,ui}.ts`
- [ ] 新建 `components/layout/AppShell.tsx`
- [ ] 更新根 `layout.tsx`，引入 ThemeProvider + 新路由组结构

### Phase 2: 用户认证（1 天）
- [ ] 实现 `(marketing)` 路由组：Landing、Login、Register
- [ ] 实现 AuthGuard（未登录重定向到 /login）
- [ ] Navbar 显示用户头像与下拉菜单
- [ ] 对接后端 `/auth/*` 和 `/users/me`

### Phase 3: 职业分析引擎（2 天）
- [ ] 重构 `analysis/page.tsx`：简历上传 → 解析 → 推荐 → 策略 → 可视化
- [ ] 实现 `SkillRadar`、`JobMatchCard`、`StrategyPanel`
- [ ] 对接 `lib/api/career.ts`

### Phase 4: 职业模拟与演化（1-2 天）
- [ ] 重构 `simulation/page.tsx`：策略选择 → 运行模拟 → 结果对比
- [ ] 实现 `PathGraph`、`StrategyCompare`
- [ ] 对接 `lib/api/simulation.ts`

### Phase 5: 交互与反馈（1 天）
- [ ] 实现 `chat/page.tsx`：SSE 流式对话
- [ ] 在 Analysis/Simulation 页面嵌入反馈收集组件
- [ ] 实现 `profile/page.tsx`：用户信息 + 操作记录

### Phase 6: 仪表盘整合（1 天）
- [ ] 重构 `dashboard/page.tsx`：移除 pipeline 信息，展示业务概览
- [ ] 整合 StatsGrid、TaskProgress、RecentActivity

### Phase 7: 清理与迁移（0.5 天）
- [ ] 标记旧文件 deprecated：`lib/t008-api.ts`、`types/t008.ts` 等
- [ ] 验证所有旧路由重定向生效
- [ ] 运行 `npm run build` 确保零错误

---

## 11. 红线约束

以下约束在重构全过程中不可违反：

1. **禁止 T00x 编号**：新代码中不得出现 T008、T009、T010、T011 等任务编号
2. **禁止构建 Agent 名称**：用户界面不得出现 parser_agent、retrieval_agent、frontend_agent 等名称
3. **禁止 Pipeline 暴露**：用户不可见 pipeline 执行步骤，Loading 状态只展示业务阶段
4. **禁止直接调用旧端点**：新页面必须通过 `lib/api/*.ts` 调用，不直接 fetch `/career/t010/run`
5. **禁止删除旧代码**：旧路由、旧端点、旧文件保留并标记 deprecated，确保向后兼容

---

*本文档经 Architect Agent 审批后生效，作为 Frontend Agent 的权威实施依据。*
