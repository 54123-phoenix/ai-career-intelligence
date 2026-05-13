# API 契约文档 v1.0

> 维护者：Architect Agent。所有跨模块数据交换必须遵守此文档。
> 版本：`1.0.0` | 生成日期：2026-05-13

---

## 目录

1. [核心数据模型](#1-核心数据模型)
2. [API 端点总览](#2-api-端点总览)
3. [L1 数据理解层](#3-l1-数据理解层)
4. [L2 模拟层](#4-l2-模拟层)
5. [L3 进化层](#5-l3-进化层)
6. [Pipeline 编排层](#6-pipeline-编排层)
7. [会话与追踪](#7-会话与追踪)
8. [用户与认证](#8-用户与认证)
9. [Chat 接口](#9-chat-接口)
10. [错误规范](#10-错误规范)
11. [弃用策略](#11-弃用策略)
12. [变更日志](#12-变更日志)

---

## 1. 核心数据模型

所有类型定义在 `backend/shared/types.py`。以下为契约层面描述，完整 Pydantic 定义以源码为准。

### 1.1 StructuredResume — 结构化简历

```
StructuredResume {
    resume_id: str            # 全局唯一标识
    name: str                 # 姓名
    email: str|null
    phone: str|null
    summary: str              # 个人总结
    skills: str[]             # 标准化技能标签
    projects: Project[]       # 项目经历
    education: Education[]    # 教育背景
    experience: WorkExperience[]  # 工作经历
    certifications: str[]     # 证书
    skill_embedding: float[]|null  # 由 Retrieval 填充
}
```

**数据流方向**：L1 Parser 产出 → L2 Simulation 消费 → L3 Evolution 消费

### 1.2 StructuredJob — 结构化岗位

```
StructuredJob {
    job_id: str
    title: str
    company: str
    location: str
    level: str                # "初级" | "中级" | "高级" | "专家"
    description: str
    required_skills: str[]
    optional_skills: str[]
    salary_range: (int, int)|null  # (min, max) K/年
    posted_date: date|null
    job_embedding: float[]|null  # 由 Retrieval 填充
}
```

### 1.3 MatchResult — 检索匹配结果

```
MatchResult {
    item_id: str              # 匹配到的 job_id 或 resume_id
    score: float [0.0, 1.0]   # Cosine 相似度
    payload: dict             # 匹配项关键字段
    match_type: "resume_to_job" | "job_to_resume" | "skill_to_skill"
}
```

**Payload 约定**：

| match_type        | 必须字段                                                   | 可选字段                              |
|-------------------|----------------------------------------------------------|-------------------------------------|
| `resume_to_job`   | `title`, `company`, `required_skills`                     | `optional_skills`, `salary_range`, `level`, `location` |
| `job_to_resume`   | `name`, `skills`                                          | `summary`, `education_level`        |
| `skill_to_skill`  | `skill_name`, `category`                                  | `market_value`                      |

### 1.4 SimulationState — 模拟状态

```
SimulationState {
    simulation_id: str
    strategy_name: str        # "aggressive" | "conservative" | "balanced"
    candidate: StructuredResume
    job: StructuredJob
    current_step: "applied"|"screened"|"interview"|"offer"|"accepted"|"rejected"|"end"
    step_count: int
    max_steps: int (=20)
    decisions: AgentDecision[]
    scores: {step_name: float}
    market_adjustment: float [0.5, 1.5]
    competition_intensity: float [0.0, 1.0]
    timestamp: str            # ISO-8601
}
```

### 1.5 AgentDecision — 单步决策

```
AgentDecision {
    agent_name: str           # "candidate"|"hr"|"market"|"interview"
    action: str               # "apply"|"screen"|"adjust"|"assess"|"accept"|"reject"
    params: dict
    reasoning: str            # 可解释理由（必填）
    confidence: float [0, 1]
    timestamp: str            # ISO-8601
}
```

### 1.6 SimulationResult — 模拟结果

```
SimulationResult {
    simulation_id: str
    strategy_name: str
    outcome: "accepted"|"rejected"|"timeout"
    final_state: SimulationState
    success_probability: float [0, 1]
    confidence_interval: (float, float)
    key_decisions: AgentDecision[]  # ≤5 条
    time_to_offer: int              # applied→offer 步数，无则为 0
    path_history: SimulationState[]
    recommendation: str
}
```

### 1.7 FinalT004Schema — simulation/run 统一响应

`simulation/run` 的实际返回类型。由 `backend/simulation/final_schema.py` 的 `build_envelope()` 构建。

```
{
    simulation_id, strategy_name, outcome,
    summary: {headline, candidate_name, job_title, company, badge, stats},
    match_score: {overall, breakdown, gauge},
    timeline: {events[], total_steps},
    skill_gap_chart: {matched[], missing[], title, match_ratio},
    recommendation_cards: [{priority, type, title, description, action_label}],
    decision_path: {title, total_actions, steps[]},
    hr_reasoning: {evaluation, score, verdict, details[], rejection_reasons[]},
    candidate_actions: {strategy, strategy_explanation, total_actions, actions[]},
    failure_points: [],
    confidence_score: {overall, factors, interpretation},
    result: SimulationResult,
    metrics: {offer_probability, skill_gap_score, total_reward}
}
```

---

## 2. API 端点总览

| 方法   | 路由                                        | 归属       | 状态       |
|--------|---------------------------------------------|-----------|-----------|
| `GET`  | `/health`                                   | 基础设施     | 已实现      |
| `POST` | `/api/v1/auth/register`                     | Auth      | MVP (内存) |
| `POST` | `/api/v1/auth/login`                        | Auth      | MVP (内存) |
| `GET`  | `/api/v1/users/me`                          | Auth      | MVP (内存) |
| `PATCH`| `/api/v1/users/me`                          | Auth      | MVP (内存) |
| `GET`  | `/api/v1/users/me/history`                  | Auth      | Mock      |
| `POST` | `/api/v1/ingestion/ingest/{source}`         | L1        | MVP (mock源) |
| `POST` | `/api/v1/ingestion/ingest/all`              | L1        | MVP (mock源) |
| `GET`  | `/api/v1/ingestion/sources`                 | L1        | 已实现      |
| `GET`  | `/api/v1/ingestion/jobs`                    | L1        | 已实现      |
| `POST` | `/api/v1/retrieval/match`                   | L1        | 已实现      |
| `POST` | `/api/v1/simulation/run`                    | L2        | MVP (样本数据) |
| `GET`  | `/api/v1/simulation/samples`                | L2        | 调试辅助    |
| `POST` | `/api/v1/feedback/review`                   | L3        | 已实现      |
| `POST` | `/api/v1/feedback/review/batch`             | L3        | 已实现      |
| `POST` | `/api/v1/feedback/training-samples`         | L3        | 已实现      |
| `GET`  | `/api/v1/feedback/samples`                  | L3        | 已实现      |
| `POST` | `/api/v1/ranking/rerank`                    | L3        | 已实现      |
| `POST` | `/api/v1/ranking/pairs`                     | L3        | 已实现      |
| `GET`  | `/api/v1/ranking/model/status`              | L3        | 已实现      |
| `GET`  | `/api/v1/ranking/model/versions`            | L3        | 已实现      |
| `POST` | `/api/v1/ranking/model/activate/{version}`  | L3        | 已实现      |
| `POST` | `/api/v1/ranking/train`                     | L3        | 已实现      |
| `POST` | `/api/v1/pipeline/run`                      | Pipeline  | 已实现      |
| `GET`  | `/api/v1/pipeline/modes`                    | Pipeline  | 已实现      |
| `GET`  | `/api/v1/pipeline/health`                   | Pipeline  | 已实现      |
| `GET`  | `/api/v1/trace/{trace_id}`                  | Trace     | 已实现      |
| `GET`  | `/api/v1/trace/`                            | Trace     | 已实现      |
| `GET`  | `/api/v1/trace/{trace_id}/samples`          | Trace     | 已实现      |
| `POST` | `/api/v1/session/start`                     | Session   | 已实现      |
| `POST` | `/api/v1/session/action`                    | Session   | 已实现      |
| `POST` | `/api/v1/session/end`                       | Session   | 已实现      |
| `GET`  | `/api/v1/session/active/{user_id}`          | Session   | 已实现      |
| `GET`  | `/api/v1/session/{session_id}`              | Session   | 已实现      |
| `GET`  | `/api/v1/session/user/{user_id}/sessions`   | Session   | 已实现      |
| `GET`  | `/api/v1/session/preferences/{user_id}`     | Session   | 已实现      |
| `POST` | `/api/v1/session/run`                       | Session   | 已实现      |
| `GET`  | `/api/v1/session/queue/status`              | Session   | 已实现      |
| `POST` | `/api/v1/career/event`                      | Career    | 已实现      |
| `GET`  | `/api/v1/career/timeline/{user_id}`         | Career    | 已实现      |
| `POST` | `/api/v1/career/analyze`                    | Career    | 已实现      |
| `POST` | `/api/v1/career/strategy`                   | Career    | 已实现      |
| `POST` | `/api/v1/career/simulate`                   | Career    | 已实现      |
| `GET`  | `/api/v1/career/visualize/{user_id}`        | Career    | 已实现      |
| `POST` | `/api/v1/career/run`                        | Career    | 已实现      |
| `GET`  | `/api/v1/career/events/{user_id}`           | Career    | 已实现      |
| `POST` | `/api/v1/chat/message`                      | Chat      | Mock (SSE) |

### 2.1 T008-T010 子路由（已弃用，由 Business Facade 替代）

| 方法   | 路由                                        | 标签                  | Sunset     |
|--------|---------------------------------------------|----------------------|------------|
| `POST` | `/api/v1/career/t008/run`                   | T008 Career Growth    | 2026-12-31 |
| `POST` | `/api/v1/career/t008/parse`                 | T008 Career Growth    | 2026-12-31 |
| `POST` | `/api/v1/career/t008/retrieve`              | T008 Career Growth    | 2026-12-31 |
| `POST` | `/api/v1/career/t008/review`                | T008 Career Growth    | 2026-12-31 |
| `POST` | `/api/v1/career/t008/architect`             | T008 Career Growth    | 2026-12-31 |
| `POST` | `/api/v1/career/t008/simulate`              | T008 Career Growth    | 2026-12-31 |
| `GET`  | `/api/v1/career/t008/frontend/{user_id}`    | T008 Career Growth    | 2026-12-31 |
| `POST` | `/api/v1/career/t009/run`                   | T009 Career Growth V2 | 2026-12-31 |
| `POST` | `/api/v1/career/t009/feedback`              | T009 Career Growth V2 | 2026-12-31 |
| `GET`  | `/api/v1/career/t009/baselines`             | T009 Career Growth V2 | 2026-12-31 |
| `POST` | `/api/v1/career/t009/trends`                | T009 Career Growth V2 | 2026-12-31 |
| `POST` | `/api/v1/career/t010/run`                   | T010 Lightweight      | 2026-12-31 |
| `GET`  | `/api/v1/career/t010/upgrade-interfaces`    | T010 Lightweight      | 2026-12-31 |

### 2.2 Business Facade（推荐前端使用）

| 方法   | 路由                                        | 描述                   |
|--------|---------------------------------------------|------------------------|
| `POST` | `/api/v1/career/analyze`                    | 职业综合分析（已复用）       |
| `POST` | `/api/v1/career/resume`                     | 简历上传与解析（占位）       |
| `POST` | `/api/v1/career/recommendations`            | 岗位推荐列表              |
| `POST` | `/api/v1/career/match-score`                | 用户-岗位匹配度查询         |
| `POST` | `/api/v1/career/path`                       | 职业路径图数据             |
| `POST` | `/api/v1/career/feedback`                   | 用户反馈提交              |
| `GET`  | `/api/v1/career/trends`                     | 行业趋势（Mock）          |

---

## 3. L1 数据理解层

### 3.1 Data Ingestion — 外部数据采集

#### `GET /api/v1/ingestion/sources`

列出已注册的数据源。

**Response 200**：
```json
{
    "sources": ["mock"],
    "total": 1
}
```

#### `POST /api/v1/ingestion/ingest/{source_name}`

从指定数据源采集并标准化岗位数据。

**Response 200**：
```json
{
    "source": "mock",
    "fetched": 12,
    "normalized": 10,
    "duplicates_skipped": 2,
    "jobs": [
        {
            "job_id": "job-001",
            "title": "Senior Backend Engineer",
            "company": "ACME Corp",
            "required_skills": ["Python", "FastAPI"]
        }
    ]
}
```

#### `GET /api/v1/ingestion/jobs`

获取已采集的岗位列表。

**Query Params**：`source` (可选), `limit` (默认 100)

**Response 200**：`UnifiedJob[]`

---

### 3.2 Retrieval — 语义检索

#### `POST /api/v1/retrieval/match`

简历 → 岗位匹配。Pipeline：编码 → Cosine 搜索 → 缺失技能计算 → Top-K。

**Request**：
```json
{
    "resume": { "resume_id": "res-001", "name": "...", "skills": ["Python"], ... },
    "top_k": 10,
    "score_threshold": 0.3
}
```

**Response 200**：
```json
{
    "matches": [
        {
            "item_id": "job-001",
            "score": 0.87,
            "payload": {
                "title": "Senior Backend Engineer",
                "company": "ACME Corp",
                "required_skills": ["Python", "FastAPI"],
                "level": "高级",
                "location": "上海"
            },
            "match_type": "resume_to_job"
        }
    ],
    "query_ms": 12.5
}
```

**错误**：
- `422` — `resume` 字段不符合 `StructuredResume` schema

---

## 4. L2 模拟层

### 4.1 Simulation — 多 Agent 博弈

#### `POST /api/v1/simulation/run`

运行单路径招聘模拟。引擎：CandidateAgent + HRAgent + 状态机。返回 FinalT004Schema。

**Request**：
```json
{
    "resume_id": "res-001",
    "job_id": "job-001",
    "strategy": "balanced"
}
```

| 参数        | 类型   | 默认值       | 可选值                                      |
|------------|--------|-------------|-------------------------------------------|
| resume_id  | str    | 必填         | `res-001`, `res-002`, `res-003` (MVP)     |
| job_id     | str    | 必填         | `job-001`, `job-002`, `job-003` (MVP)     |
| strategy   | str    | `"balanced"` | `"aggressive"`, `"conservative"`, `"balanced"` |

**Response 200**：`FinalT004Schema` — 参见 [1.7 节](#17-finalt004schema--simulationrun-统一响应)

**错误**：
- `404` — `resume_id` 或 `job_id` 不在样本库中。返回可用 ID 列表。
- `422` — 参数类型或枚举值不合法

**当前限制**：使用内存中的 3 份样本简历和 3 个样本岗位，未对接 Parser/Retrieval 的实际数据。

#### `GET /api/v1/simulation/samples`

列出可用的样本 resume / job ID（调试用）。

**Response 200**：
```json
{
    "resumes": {"res-001": "Alice Wang", "res-002": "Bob Zhang", "res-003": "Carol Li"},
    "jobs": {"job-001": "Senior Backend Engineer @ ACME Corp", ...}
}
```

---

## 5. L3 进化层

### 5.1 Feedback — 反馈采集与审阅

#### `POST /api/v1/feedback/review`

审阅单次模拟结果，生成 FeedbackEntry（含 retrieval_reward、ranking_penalty、bias_flags）。

**Request**：
```json
{
    "simulation_result": { ... },
    "retrieval_matches": []
}
```

**Response 200**：
```json
{
    "entry_id": "fe-...",
    "simulation_id": "sim-...",
    "retrieval_reward": 0.85,
    "ranking_penalty": 0.0,
    "combined_signal": 0.85,
    "bias_flags": []
}
```

#### `POST /api/v1/feedback/review/batch`

批量审阅。返回 FeedbackAggregate（逐条 review + 批次级偏置检测）。

**Response 200**：
```json
{
    "batch_id": "fb-...",
    "entries": [ ... ],
    "summary": { "avg_signal": 0.78, "total_flagged": 1 },
    "bias_findings": []
}
```

#### `POST /api/v1/feedback/training-samples`

从 review + simulation 输出生成 LTR 训练数据集。过滤低质量样本（label < 0.1 或空 feature）。

**Response 200**：`TrainingSample[]`

#### `GET /api/v1/feedback/samples?limit=50`

获取本会话累积的 training samples。

---

### 5.2 Ranking — LTR 排序

#### `POST /api/v1/ranking/rerank`

对检索候选集应用排序模型。无训练模型时返回 identity 结果。

**Request**：
```json
{
    "trace_id": "trace-...",
    "candidates": [
        {"item_id": "job-001", "score": 0.87, "payload": {...}, "match_type": "resume_to_job"}
    ],
    "user_profile": { ... },
    "interaction_history": []
}
```

**Response 200**：`RerankedCandidate[]`

#### `POST /api/v1/ranking/pairs`

从用户行为日志生成 pairwise 排序样本。规则：clicked > skipped, saved > clicked。禁止 self-pair。

**Response 200**：`RankingPair[]`

#### `GET /api/v1/ranking/model/status`

```json
{
    "active": true,
    "model": { ... },
    "versions_count": 3
}
```

#### `GET /api/v1/ranking/model/versions`

`TrainedRankerModel[]` — 所有已存储模型版本，最新优先。

#### `POST /api/v1/ranking/model/activate/{version}`

激活指定版本用于 rerank。

**错误**：`404` — 版本号不存在

#### `POST /api/v1/ranking/train`

离线批量训练排序模型。可指定 `from_recent_traces` 从最近 trace 提取 pairs。

**Request**：
```json
{
    "pairs": [],
    "validation_split": 0.2,
    "from_recent_traces": true,
    "days": 7
}
```

---

## 6. Pipeline 编排层

### 6.1 Pipeline — 统一执行入口

#### `POST /api/v1/pipeline/run`

执行完整多 Agent 闭环流水线。返回 InteractionTrace — 链接所有阶段输出的统一追踪记录。

**Request**：
```json
{
    "user_query": "",
    "user_embedding": null,
    "filters": null,
    "mode": null,
    "interaction_history": null,
    "user_id": null,
    "session_id": null
}
```

| 参数                 | 类型             | 描述                                          |
|----------------------|-----------------|-----------------------------------------------|
| `user_query`         | str             | 自然语言搜索查询                                  |
| `user_embedding`     | float[]\|null   | 预计算的查询向量                                  |
| `filters`            | dict\|null      | `{"location": "北京", "skill": "Python"}`       |
| `mode`               | str\|null       | 不填=Architect 自动选择；填=强制模式                 |
| `interaction_history`| list\|null      | 用户行为日志（RANKING 模式使用）                     |
| `user_id`            | str\|null       | 用户标识（SESSION 模式使用）                        |
| `session_id`         | str\|null       | 已有会话 ID（SESSION 模式使用）                     |

**执行模式**：

| 模式       | Pipeline                                                | 触发条件                       |
|-----------|---------------------------------------------------------|-------------------------------|
| `fast`    | 缓存检索 → 最小模拟 → review → feedback                     | 热缓存，简单查询                   |
| `full`    | retrieval → simulation → review → feedback              | 正常操作，复杂查询                  |
| `fallback`| 降级：缓存或纯 API，跳过 simulation                          | 核心服务降级                      |
| `ranking` | retrieval → feature_build → rerank → review → pair_build | 训练模型可用 + 用户行为数据可用         |
| `session` | session_track → aggregate → update_prefs → retrieval → rerank → review → feedback_queue → feedback | 用户会话 + 动态偏好需求             |
| `career`  | parse → retrieve → review → architect → simulate → frontend | 长期职业分析                      |

**Response 200**：`InteractionTrace`
```json
{
    "trace_id": "trace-...",
    "mode": "full",
    "user_query": "...",
    "retrieved_candidates": [ ... ],
    "simulation_results": [ ... ],
    "training_samples": [ ... ],
    "errors": [],
    "elapsed_ms": 1234.5
}
```

**错误**：`500` — Pipeline 执行异常（含详情 message）

#### `GET /api/v1/pipeline/modes`

列出所有可用模式和描述。

#### `GET /api/v1/pipeline/health`

流水线健康检查。返回各服务状态（`ok` / `degraded`）。

---

## 7. 会话与追踪

### 7.1 Session — 用户会话

#### `POST /api/v1/session/start`
```json
// Request
{"user_id": "usr-abc"}

// Response 200
{"session_id": "sess-...", "user_id": "usr-abc", "is_active": true}
```
自动结束该用户已有的活跃会话。

#### `POST /api/v1/session/action`
```json
// Request
{
    "session_id": "sess-...",
    "action": {
        "action_type": "query",
        "query_text": "Python 后端岗位",
        "timestamp": "2026-05-13T12:00:00Z"
    }
}

// Response 200
{"session": {...}, "summary": {"total_actions": 5, "top_skills": ["Python"], ...}}
```

#### `POST /api/v1/session/end`
```json
// Request  {"user_id": "usr-abc"}
// Response 200  Session 对象
```
**错误**：`404` — 无活跃会话

#### `GET /api/v1/session/active/{user_id}`

获取当前活跃会话。无则自动创建。

#### `GET /api/v1/session/{session_id}`

获取指定会话详情。**错误**：`404` — 不存在

#### `GET /api/v1/session/user/{user_id}/sessions?limit=20`

列出用户最近会话。

#### `GET /api/v1/session/preferences/{user_id}`

```json
{
    "preferences": {"preferred_skills": ["Python"], ...},
    "session_summary": {...},
    "session_count": 12,
    "shift_score": 0.15
}
```

#### `POST /api/v1/session/run`

执行完整 SESSION 流水线（8 阶段）。

#### `GET /api/v1/session/queue/status`

```json
{"pending_events": 42, "max_events": 10000}
```

---

### 7.2 Trace — 交互追踪

#### `GET /api/v1/trace/{trace_id}`

获取完整 InteractionTrace。**错误**：`404` — 不存在或已过期。

#### `GET /api/v1/trace/?limit=50`

列出最近 trace 摘要（trace_id, mode, query, candidates_count, elapsed_ms）。

#### `GET /api/v1/trace/{trace_id}/samples`

仅获取某 trace 的 training samples。

---

## 8. 用户与认证

当前为 MVP 内存实现。生产环境需替换为数据库 + bcrypt + JWT。

### 8.1 Auth

#### `POST /api/v1/auth/register`

```json
// Request
{"email": "user@example.com", "password": "****", "name": "张三"}

// Response 200
{
    "token": "sess-...",
    "user": {
        "user_id": "usr-abc12345",
        "email": "user@example.com",
        "name": "张三",
        "skills": [],
        "career_goals": [],
        "privacy_level": "basic"
    }
}
```
**错误**：`400` — 邮箱已注册

#### `POST /api/v1/auth/login`

```json
// Request  {"email": "user@example.com", "password": "****"}
// Response 200  {"token": "...", "user": {...}}
```
**错误**：`401` — 邮箱或密码无效

### 8.2 User Profile

所有 User 路由需 Bearer Token 认证（`Authorization: Bearer <token>`）。

#### `GET /api/v1/users/me`

获取当前用户信息。**错误**：`401` — 未认证

#### `PATCH /api/v1/users/me`

更新用户信息。
```json
// Request
{
    "name": "张三（更新）",
    "skills": ["Python", "Go"],
    "experience_years": 5
}
```

#### `GET /api/v1/users/me/history?page=1&limit=20`

用户操作历史（当前为 Mock 数据）。

---

## 9. Chat 接口

#### `POST /api/v1/chat/message`

AI 职业助手 — SSE 流式响应。

**Request**：
```json
{
    "message": "我想转行做 AI 工程师",
    "conversation_id": null,
    "context": null
}
```

**Response**：`Content-Type: text/plain; charset=utf-8` + `Transfer-Encoding: chunked`

流式传输 UTF-8 文本块，客户端逐块解码拼接。

**当前状态**：Mock 实现，返回预制中文建议文本。`backend/shared/llm_client.py` 已提供 `register_llm()` 注入点，生产环境替换 `_mock_stream()` 即可。

---

## 10. 错误规范

所有错误响应格式：

```json
{
    "detail": "人类可读的错误描述"
}
```

| 状态码 | 含义       | 触发场景                     |
|--------|-----------|----------------------------|
| `400`  | 请求错误    | 缺少必要字段、邮箱已注册、事件列表为空  |
| `401`  | 未认证      | 缺少或无效 Bearer Token       |
| `404`  | 资源不存在   | resume/job/session/trace ID 无效 |
| `422`  | 参数校验失败 | Pydantic 模型验证不通过          |
| `500`  | 服务器错误   | Pipeline 异常、Agent 执行失败    |

---

## 11. 弃用策略

以下端点已在响应头中标记 `Deprecation: true` + `Sunset: 2026-12-31`（由 `main.py` 的 `deprecation_middleware` 统一注入）：

- `* /api/v1/career/t008/*` — 由 Business Facade 替代
- `* /api/v1/career/t009/*` — 由 Business Facade 替代
- `* /api/v1/career/t010/*` — 由 Business Facade 替代

前端应在 Sunset 日期前迁移至 Business Facade 端点（`/api/v1/career/analyze`, `/recommendations`, `/match-score`, `/path`, `/feedback`）。

---

## 12. 变更日志

| 版本   | 日期       | 变更内容                                                      |
|--------|-----------|---------------------------------------------------------------|
| 1.0.0  | 2026-05-13 | 初始完整版本：覆盖全部 12 个路由模块、7 个核心数据模型、Business Facade、错误规范、弃用策略 |

### 模块契约索引

| 模块          | 源码路径                        | 契约定义位置                |
|--------------|------------------------------|---------------------------|
| L1 Parser    | `backend/parser/`             | StructuredResume/Job in shared/types.py |
| L1 Ingestion | `backend/data_ingestion/`     | 本节 3.1                   |
| L1 Retrieval | `backend/retrieval/`          | 本节 3.2                   |
| L2 Simulation| `backend/simulation/`         | 本节 4.1                   |
| L3 Feedback  | `backend/feedback/`           | 本节 5.1                   |
| L3 Ranking   | `backend/ranking/`            | 本节 5.2                   |
| Pipeline     | `backend/pipeline/`           | 本节 6.1                   |
| Session      | `backend/session/`            | 本节 7.1                   |
| Trace        | `backend/signal_layer/`       | 本节 7.2                   |
| Auth         | `backend/api/routes/auth.py`  | 本节 8                     |
| Chat         | `backend/api/routes/chat.py`  | 本节 9                     |
| Career       | `backend/career/`             | 本节 2.2                   |
