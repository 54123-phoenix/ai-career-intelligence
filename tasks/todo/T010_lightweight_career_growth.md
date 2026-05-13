---
id: T-010
status: done
assignee: orchestrator
type: feature
created: 2026-05-12
---

# T010：轻量化职业成长系统 — 核心层 + 升级接口

## 目标
在 T009 基础上裁剪为核心层（单用户、轻量化），并为每个 Agent 明确标注升级接口。

## 设计模式：核心层 + 升级接口

每个 Agent 输出均携带 `UpgradeInterface` 元数据：
- `core_capability`：当前核心层能力
- `upgrade_hooks`：命名扩展点列表
- `upgrade_notes`：每个扩展点的实现指南

## 输出
- [x] `backend/career/t010_schemas.py` — UpgradeInterface + 6 个 Agent 输出包装类
- [x] `backend/career/t010_pipeline.py` — T010Pipeline（核心层，限制 3-5 candidates，≤10 模拟轮次，2 RL 迭代）
- [x] `backend/career/__init__.py` — T010 导出
- [x] `backend/api/routes/career.py` — 2 个 T010 端点（run, upgrade-interfaces）
- [x] `frontend/types/t010.ts` — T010 TypeScript 接口
- [x] `frontend/lib/t010-api.ts` — T010 API 客户端
- [x] `frontend/app/career/growth-lite/page.tsx` — T010 轻量页面

## 核心约束

| 参数 | T009 | T010 |
|------|------|------|
| 候选策略数 | 无硬限制 | **3-5** |
| 模拟轮次 | 10 | **≤10** |
| RL 迭代 | 3 | **2** |
| 学习率 | 0.05 | **0.03** |
| 用户范围 | 单用户 | 单用户（显式） |
| 前端标签 | 7 个 | **5 个** |

## 升级接口总览

| Agent | 核心能力 | 升级钩子 |
|-------|---------|---------|
| parser | 单用户画像 + baseline 匹配 | multi_user_ingest, multi_source_aggregation, cross_domain_mapping |
| retrieval | 单用户岗位匹配 + 3-5 策略 | cross_user_strategy_library, multi_industry_retrieval, strategy_graph_search |
| reviewer | 单用户 5 维评分 + RL 权重 | group_pattern_scoring, multi_dim_metric_expansion, cohort_benchmark_comparison |
| architect | 单用户路径图 + 趋势叠加 | multi_scenario_simulation, long_term_trend_overlay, group_strategy_overlay |
| simulation | 短期模拟 + 高置信度优先 | multi_scenario_long_term, multi_user_cohort_sim, market_shock_scenario |
| frontend | 单用户图表 + 隐私脱敏 | multi_user_view, cohort_comparison, trend_overlay_view |
