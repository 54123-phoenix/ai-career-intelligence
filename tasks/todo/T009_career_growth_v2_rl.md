---
id: T-009
status: done
assignee: orchestrator
type: feature
created: 2026-05-12
---

# T009：职业成长系统 V2 — RL 优化与反馈闭环

## 目标
在 T008 基础上增加 6 项增强：baseline 模板匹配（冷启动）、5 维多样性评分、RL 动态权重迭代、偏离路径检测、行业趋势整合、数据脱敏与反馈回流。

## 输出
- [x] `backend/career/t009_schemas.py` — 14 个新增/扩展 Pydantic 模型
- [x] `backend/career/t009_pipeline.py` — T009Pipeline（RL 迭代、baseline 匹配、off-path 检测、privacy）
- [x] `backend/career/__init__.py` — T009 导出
- [x] `backend/api/routes/career.py` — 5 个 T009 API 端点
- [x] `frontend/types/t009.ts` — T009 TypeScript 接口
- [x] `frontend/lib/t009-api.ts` — T009 API 客户端
- [x] `frontend/app/career/growth-v2/page.tsx` — T009 主页面（交互式节点、隐私开关、RL 状态、反馈提交）

## T009 vs T008 对比

| 特性 | T008 | T009 |
|------|------|------|
| 评分维度 | 4 (成功率, 匹配度, 成长周期, 技能适配) | 5 (+多样性) |
| 权重机制 | 固定 (0.35/0.30/0.20/0.15) | RL 动态更新, 收敛检测 |
| 冷启动 | 无 | 5 条行业 baseline 模板 |
| 路径异常 | 无 | 4 类 off-path flag |
| 行业趋势 | 无 | TrendReport → architect 调整 |
| 反馈闭环 | 单向 | 双向 (frontend → parser + reviewer) |
| 数据安全 | 无 | 3 级隐私脱敏 |
| 候选策略数 | 无限制 | 3-5 条限制 |
| 模拟迭代 | 固定 10 轮 | 3 RL 迭代 × 10 模拟轮 |
| 过拟合防护 | 无 | DiversityMetric + 多样性权重 |
