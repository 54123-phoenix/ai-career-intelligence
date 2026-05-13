---
id: T-003
status: todo
assignee: simulation_agent
type: feature
created: 2025-01-15
---

# 设计 Simulation Engine 与基础 Agent 行为

## 目标
实现 `backend/simulation/` 模块，包含 BaseAgent 抽象、CandidateAgent / HRAgent / MarketAgent 初步实现、LangGraph StateGraph 编排。

## 输入
- 上游依赖：T-001, T-002（结构化数据 + 检索结果）
- 参考文档：
  - `docs/api_contracts.md` → SimulationState / SimulationResult / AgentDecision
  - `docs/system_flow.md` → 状态机转换条件

## 输出
- `backend/simulation/base_agent.py` —— Agent 抽象基类
- `backend/simulation/agents/candidate_agent.py`
- `backend/simulation/agents/hr_agent.py`
- `backend/simulation/agents/market_agent.py`
- `backend/simulation/engine.py` —— LangGraph StateGraph 编排
- `backend/simulation/state.py` —— 状态定义
- `tests/test_simulation.py` —— 单元测试
- `data/simulation_samples/sample_result.json` —— 模拟结果示例

## 约束
- 使用 LangGraph `StateGraph` 定义流程
- 所有 Agent 通过 `SimulationState` 交互，禁止直接修改其他 Agent 状态
- 支持 seed 固定，保证可复现
- Agent 决策必须附带 `reasoning` 字段（可解释性）
- 模拟最大步数 20 步，超时自动返回中间状态

## 验收标准
- [ ] `SimulationEngine.run()` 能从 `Applied` 走到 `Accepted/Rejected`
- [ ] 同一输入 + 同一 seed 产出相同结果
- [ ] CandidateAgent / HRAgent / MarketAgent 各至少 2 个测试用例
- [ ] 状态转换符合 `docs/system_flow.md` 定义
- [ ] 模拟结果包含 `success_probability` 和 `confidence_interval`
