# 系统流程与状态转换

> 由 @architect_agent 维护。描述 Simulation Layer (L2) 的完整状态机与数据流。
> 版本：`2.0.0`

---

## 1. 状态机定义（SimulationState）

### 核心状态对象

```
SimulationState {
    simulation_id: str            # 全局唯一
    strategy_name: str            # "aggressive" | "conservative" | "balanced"

    candidate: StructuredResume   # 不可变实体
    job: StructuredJob            # 不可变实体

    current_step: "applied" | "screened" | "interview" | "offer" | "accepted" | "rejected" | "end"
    step_count: int               # 已执行的 Agent 动作次数
    max_steps: int = 20           # 安全上限

    decisions: AgentDecision[]    # 追加-只读审计轨迹
    scores: {step_name: float}    # {"hr_screen": 0.8, "interview": 0.65, "final": 0.72}

    market_adjustment: float      # [0.5, 1.5]  供需修正
    competition_intensity: float  # [0.0, 1.0]  竞争强度

    timestamp: str                # ISO-8601 最后更新时间
}
```

### AgentDecision（单条决策记录）

```
AgentDecision {
    agent_name: "candidate" | "hr" | "market" | "interview"
    action: str                   # "apply" | "screen" | "adjust" | "assess" | "accept" | "reject"
    params: dict                  # 动作参数
    reasoning: str                # 可解释决策理由（必填）
    confidence: float             # [0, 1] Agent 自身置信度
    timestamp: str                # ISO-8601
}
```

---

## 2. 状态转换图（文字版）

```
                    ┌──────────┐
                    │ applied  │  ← CandidateAgent: 提交申请
                    │  step=0  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ screened │  ← HRAgent: 简历初筛
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         hard_pass    score >=     score <
         = false      threshold    threshold
              │          │          │
              │     ┌────▼────┐     │
              │     │interview│     │
              │     └────┬────┘     │
              │          │          │
              │     ┌────┼────┐     │
              │     │    │    │     │
              │  pass  fail  │     │
              │     │    │    │     │
              │  ┌──▼──┐ │   │     │
              │  │offer│ │   │     │
              │  └──┬──┘ │   │     │
              │     │    │    │     │
              │  ┌──┼────┼────┼──┐  │
              │  │  │    │    │  │  │
              │ accept │ reject │  │
              │  │     │    │   │  │
              └──┼─────┴────┴───┼──┘
                 │              │
            ┌────▼───┐    ┌─────▼───┐
            │accepted│    │rejected  │
            └────────┘    └──────────┘
                 │              │
                 └──────┬───────┘
                        │
                    ┌───▼──┐
                    │ end  │
                    └──────┘
```

### 转换条件表

| 转换 | 触发 Agent | 条件 | 概率修正 |
|------|-----------|------|---------|
| applied → screened | HRAgent | 自动进入 | — |
| screened → interview | HRAgent | `hr_score >= 0.4 AND NOT hard_pass` | × `market_adjustment` |
| screened → rejected | HRAgent | `hard_pass == true` OR `hr_score < 0.4` | — |
| interview → offer | InterviewAgent | `interview_score >= 0.6` | × `competition_intensity` |
| interview → rejected | InterviewAgent | `interview_score < 0.6` | — |
| offer → accepted | CandidateAgent | `strategy_alignment_score >= 0.5` | 策略相关 |
| offer → rejected | CandidateAgent | `strategy_alignment_score < 0.5` | 策略相关 |
| any → rejected | — | `step_count > max_steps`（超时） | — |

### 概率传播公式

```
P(offer) = P(screened → interview)
         × P(interview → offer)
         × market_adjustment

P(screened → interview) = hr_score (0-1, HRAgent 输出)
P(interview → offer)    = interview_score × (1 - competition_intensity)
```

---

## 3. 主流程序列

```
用户                          Frontend              FastAPI            Simulation Engine
 │                               │                     │                     │
 │  上传简历                      │                     │                     │
 │──────────────────────────────→│                     │                     │
 │                               │  POST /parser/resume│                     │
 │                               │────────────────────→│                     │
 │                               │                     │  parse_resume()     │
 │                               │   StructuredResume  │←────────────────────│
 │                               │←────────────────────│                     │
 │  预览解析结果                   │                     │                     │
 │←──────────────────────────────│                     │                     │
 │                               │                     │                     │
 │  点击"匹配"                    │                     │                     │
 │──────────────────────────────→│                     │                     │
 │                               │  POST /retrieval/match                    │
 │                               │────────────────────→│                     │
 │                               │                     │  match_from_store() │
 │                               │   MatchResult[]     │←────────────────────│
 │                               │←────────────────────│                     │
 │  展示岗位列表                   │                     │                     │
 │←──────────────────────────────│                     │                     │
 │                               │                     │                     │
 │  选择岗位"模拟推演"             │                     │                     │
 │──────────────────────────────→│                     │                     │
 │                               │  POST /simulation/run                    │
 │                               │────────────────────→│                     │
 │                               │                     │  run_simulation()   │
 │                               │                     │                     │
 │                               │                     │  applied            │
 │                               │                     │    → HRAgent.screen │
 │                               │                     │    → MarketAgent     │
 │                               │                     │    → InterviewAgent  │
 │                               │                     │    → CandidateAgent  │
 │                               │                     │    → accepted/end    │
 │                               │                     │                     │
 │                               │   SimulationResult  │←────────────────────│
 │                               │←────────────────────│                     │
 │  可视化模拟结果                 │                     │                     │
 │←──────────────────────────────│                     │                     │
```

---

## 4. 多路径对比

```
           相同起点: resume + job
                    │
        ┌───────────┼───────────┐
        │           │           │
   Strategy A   Strategy B   Strategy C
  "aggressive" "conservative" "balanced"
        │           │           │
        ▼           ▼           ▼
   SimResult A  SimResult B  SimResult C
   P=0.65       P=0.82       P=0.75
   T=7天        T=21天       T=14天
        │           │           │
        └───────────┼───────────┘
                    │
            ┌───────▼───────┐
            │ 对比分析       │
            │ recommendation │
            └───────────────┘
```

### 三种预设策略

| 策略 | candidate_confidence | 行为 | 预期 P(offer) | 预期 T |
|------|---------------------|------|-------------|--------|
| aggressive | 0.9 | 快速投递，跳过部分准备 | 低~中 | 短 |
| conservative | 0.4 | 先学习后投递，全程准备 | 高 | 长 |
| balanced | 0.65 | 适度准备 + 按时投递 | 中~高 | 中 |

---

## 5. SimulationResult 输出结构

```
SimulationResult {
    simulation_id: str
    strategy_name: str
    outcome: "accepted" | "rejected" | "timeout"

    final_state: SimulationState    # 最终状态快照

    success_probability: float      # [0, 1] 综合估算 P(offer)
    confidence_interval: (float, float)  # 上下界

    key_decisions: AgentDecision[]  # 关键决策点（≤5条）
    time_to_offer: int              # applied → offer 步数，无则为 0

    path_history: SimulationState[] # 每步完整快照
    recommendation: str             # 策略建议
}
```

---

## 6. L3 反馈闭环

```
SimulationResult ──→ FeedbackCollector ──→ RewardSignal
                                               │
                    ┌──────────────────────────┘
                    ▼
              RewardEvaluator
              reward = α × success_rate
                     + β × time_efficiency
                     + γ × match_improvement
                     + δ × novelty_bonus
                    │
                    ▼
              PolicyUpdater (moving average, baseline comparison)
                    │
                    ▼
              更新 Agent 行为参数 + Skill Graph 权重
                    │
                    ▼
              下一次模拟（闭环）
```

### RewardSignal（v2.0.0）

```
RewardSignal {
    simulation_id: str
    strategy_name: str
    match_improvement: float    # 技能匹配度提升
    success_rate: float         # 该策略历史成功率
    path_efficiency: float      # 时间/收益比
    novelty_bonus: float        # 探索新策略鼓励
    total_reward: float         # 加权求和结果
}
```

---

## 7. 错误处理

| 异常 | 策略 | 返回 |
|------|------|------|
| `SimulationTimeout` (>max_steps) | 立即终止，返回 `outcome="timeout"` | 中间状态 + 部分结果 |
| Agent LLM 调用失败 | 使用规则回退决策，confidence=0.3 | 标注回退的 AgentDecision |
| HR hard_pass 触发 | 直接跳转 rejected | 完整路径（applied→screened→rejected） |
| 嵌入为空 | Simulation 调用 Retrieval 编码 | — |
