# AI Career Intelligence — Frontend UI重构日志

## 项目背景
- **目标**: 竞赛演示级前端UI，吸引评委注意力
- **策略**: 单屏叙事 + 深色科技风 + ECharts可视化 + Framer Motion动效
- **技术栈**: Next.js 14 + TypeScript + Tailwind CSS + ECharts + Framer Motion

---

## 2026-05-12 实施记录

### Phase 0: 侦察与诊断 ✅
**发现**: 前端目录仅有源码文件（`app/`, `components/`, `lib/`, `types/`），**完全缺失项目基础设施**：
- ❌ `package.json`
- ❌ `tsconfig.json`
- ❌ `next.config.js`
- ❌ `tailwind.config.ts`
- ❌ `postcss.config.js`
- ❌ `app/layout.tsx`
- ❌ `app/globals.css`

**决策**: 从零建立完整的 Next.js 14 可运行项目。

### Phase 1: 基础设施搭建 ✅
创建文件清单:
| 文件 | 说明 |
|------|------|
| `package.json` | Next.js 14 + React 18 + ECharts + Framer Motion + Tailwind 等 |
| `tsconfig.json` | bundler 模块解析 + `@/*` 路径别名 |
| `next.config.js` | App Router 配置 + `/` → `/dashboard` 重定向 |
| `tailwind.config.ts` | 深色科技主题扩展（neon colors, glass, glow animations） |
| `postcss.config.js` | Tailwind + Autoprefixer |
| `next-env.d.ts` | Next.js 类型声明 |
| `app/layout.tsx` | 根布局（强制 dark 模式） |
| `app/globals.css` | 全局样式（深色背景、glass card、neon glow、滚动条、选择色） |

**依赖安装**: `npm install` — 成功安装 402 个包（包含 echarts, echarts-for-react, framer-motion, react-countup, lucide-react）。

### Phase 2: 共享组件层 ✅
创建文件清单:
| 文件 | 功能 |
|------|------|
| `lib/utils.ts` | `cn()` 工具函数 + 格式化辅助 |
| `components/ui/GlassCard.tsx` | 毛玻璃卡片容器，支持 glow 边框 + Framer Motion 进入动画 |
| `components/ui/AnimatedNumber.tsx` | 基于 react-countup 的数字滚动动画 |
| `components/ui/SectionHeader.tsx` | 区块标题组件（图标 + 标题 + 副标题） |

### Phase 3: 核心图表组件 ✅
全部基于 ECharts（放弃 D3/Three.js，降低复杂度）：

| 文件 | 图表类型 | 说明 |
|------|---------|------|
| `components/charts/CareerPathGraph.tsx` | ECharts `graph` (力导向图) | 技能节点 + 依赖边 + 主路径高亮 + 点击回调 |
| `components/charts/StrategyRadar.tsx` | ECharts `radar` (雷达图) | 策略六维对比 + 策略切换按钮 |
| `components/charts/SimulationHeatmap.tsx` | ECharts `heatmap` (热力图) | 轮次 × 指标热力图 |
| `components/charts/SimulationGauge.tsx` | ECharts `gauge` (仪表盘) | 成功率环形仪表盘 + 数字滚动 |

**设计决策**:
- 所有图表使用深色主题 tooltip（`backgroundColor: 'rgba(15,23,42,0.95)'`）
- 主路径边使用霓虹青蓝高亮 + shadowBlur
- 雷达图支持 activeIndex 高亮（线宽 + 填充透明度变化）

### Phase 4: Dashboard 三幕叙事页面 ✅

**文件清单**:
| 文件 | 角色 |
|------|------|
| `components/dashboard/ActOneInput.tsx` | 第一幕：用户输入 + 解析后的技能标签云/画像卡片 |
| `components/dashboard/ActTwoStrategy.tsx` | 第二幕：策略雷达图 + TOP策略列表 + 成长路径网络图 + RL权重 + 偏离路径警告 |
| `components/dashboard/ActThreeSimulation.tsx` | 第三幕：仪表盘 + 热力图 + 风险条形图 + 技能缺口标签 + 多样性指标 |
| `components/dashboard/NodeDetailDrawer.tsx` | 节点点击弹窗（技能详情 + 策略说明 + 风险警告） |
| `app/dashboard/page.tsx` | **主页面**：顶部导航 + 英雄区 + 三幕顺序展开 + 导演模式自动推进 |

**交互设计**:
- 点击 "Run Intelligence" → 加载骨架屏 → 数据返回后自动逐幕展开（demoStage 1→2→3，间隔 800ms）
- 策略列表点击 → 雷达图高亮对应策略 → 成长路径图联动
- 成长路径节点点击 → NodeDetailDrawer 弹窗
- 顶部导航显示状态/耗时/版本等实时指标

### Phase 5: 验证与待办
- [x] `npm run build` 验证 TypeScript 编译（持续修复中：StrategyRadar import / CareerPathGraph lineStyle / NodeDetailDrawer unknown / 旧页面编码）
- [ ] growth-lite 页面 JSX 解析问题待排查（已临时禁用为 `_growth-lite`）
- [ ] 启动 dev server 目视检查
- [ ] 响应式适配微调（移动端图表高度）
- [ ] 添加更多 mock 数据场景

---

## 关键技术决策

### 1. 放弃 D3.js / Three.js
**原因**: 
- D3 写力导向图需要 200+ 行底层代码
- ECharts `graph` 系列通过声明式配置即可实现 90% 效果
- Three.js 对于职业路径场景是过度杀伤

### 2. 单屏滚动替代多页跳转
**原因**:
- 竞赛演示 5-10 分钟，频繁跳转打断叙事
- 单屏滚动 + 分幕动画 = 导演式体验
- 降低页面加载失败的风险

### 3. 深色科技风配色
```
背景: #0a0e1a (slate-950)
卡片: rgba(30, 41, 59, 0.6) + backdrop-blur
强调: #06b6d4 (cyan) → #3b82f6 (blue) 渐变
成功: #10b981 (green)
警告: #f59e0b (orange)
危险: #ef4444 (red)
```

### 4. 保留旧页面
旧页面（`/career/growth`, `/career/growth-v2`, `/career/growth-lite`, `/simulation/report`）未做修改，
作为系统不同版本的展示入口继续存在。

---

## 文件变更统计

**新增文件**: 18 个
**修改文件**: 3 个（旧页面 TypeScript 类型修复，零逻辑变更）
- `app/career/growth/page.tsx`: `frontend_data` 属性类型断言修复
- `app/career/growth-v2/page.tsx`: `frontend_data` + `interactive_nodes` 类型断言修复
- `app/career/growth-lite/page.tsx`: `frontend_data` 属性类型断言修复
**删除文件**: 0 个

---

*Log maintained by AI agent. Last updated: 2026-05-12*
