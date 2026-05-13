---
id: T-008
status: in_progress
assignee: orchestrator
type: feature
created: 2026-05-12
---

# T008：职业成长系统收敛与策略优化

## 目标
实现 6-agent 职业成长收敛管道：parser → retrieval → reviewer → architect → simulation → reviewer(re-rank) → frontend

## 输出
- [x] `backend/career/t008_schemas.py` — T008 Pydantic schemas (UserProfile, CareerData, ScoredStrategy, CareerPlan, VisualizationGraph, SimulationFeedback, T008PipelineOutput)
- [x] `backend/career/t008_pipeline.py` — T008Pipeline 6-agent orchestrator with multi-round simulation
- [x] `backend/career/__init__.py` — Updated exports for T008 types
- [x] `backend/api/routes/career.py` — T008 API endpoints (/api/v1/career/t008/*)
- [x] `frontend/types/t008.ts` — TypeScript interfaces aligned with backend
- [x] `frontend/lib/t008-api.ts` — API client for T008 endpoints
- [x] `frontend/components/career/StrategyComparison.tsx` — Strategy radar/bar comparison
- [x] `frontend/components/career/CareerPathGraph.tsx` — Skill tree + timeline visualization
- [x] `frontend/components/career/SimulationFeedback.tsx` — Multi-round simulation chart
- [x] `frontend/components/career/CareerPlanTimeline.tsx` — Gantt-like action timeline
- [x] `frontend/components/career/index.ts` — Barrel exports
- [x] `frontend/app/career/growth/page.tsx` — T008 main page

## 验收
- [ ] API endpoints return correct T008PipelineOutput schema
- [ ] 6-agent pipeline executes without errors
- [ ] Multi-round simulation returns proper SimulationFeedback
- [ ] Frontend renders all 5 visualization tabs
- [ ] Strategy scoring uses all 4 dimensions (success_rate, match_degree, growth_cycle, skill_adaptability)
- [ ] Reviewer re-rank incorporates simulation feedback
