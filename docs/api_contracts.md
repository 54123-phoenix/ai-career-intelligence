# API 契约文档

> 由 @architect_agent 维护。所有跨模块数据交换必须遵守此文档定义的契约。
> 版本：`1.0.0`

---

## 核心数据模型

### StructuredResume（结构化简历）

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date

class Project(BaseModel):
    name: str = Field(description="项目名称")
    description: str = Field(default="", description="项目描述")
    tech_stack: list[str] = Field(default_factory=list, description="技术栈")
    start_date: date | None = None
    end_date: date | None = None

class Education(BaseModel):
    school: str
    degree: Literal["本科", "硕士", "博士", "其他"]
    major: str
    graduation_year: int | None = None

class WorkExperience(BaseModel):
    company: str
    title: str
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None

class StructuredResume(BaseModel):
    """L1 Parser 输出 → L2 Simulation / L3 Evolution 输入"""
    resume_id: str = Field(description="全局唯一标识")
    name: str
    email: str | None = None
    phone: str | None = None
    summary: str = ""
    skills: list[str] = Field(default_factory=list, description="标准化后的技能标签")
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    experience: list[WorkExperience] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    skill_embedding: list[float] | None = None  # 由 Retrieval 模块填充

    class Config:
        json_schema_extra = {
            "example": {
                "resume_id": "res-001",
                "name": "张三",
                "skills": ["Python", "FastAPI", "LangChain"],
                "projects": [{"name": "AI招聘系统", "tech_stack": ["Python", "React"]}]
            }
        }
```

### StructuredJob（结构化岗位）

```python
class StructuredJob(BaseModel):
    """L1 Parser 输出 → L2 Simulation 输入 v1.0.0"""
    job_id: str
    title: str
    company: str
    location: str = ""
    level: str = ""
    description: str = ""

    # Skills
    required_skills: list[str] = Field(default_factory=list)
    optional_skills: list[str] = Field(default_factory=list)

    # Compensation
    salary_range: tuple[int, int] | None = None  # (min, max) K/年

    # Metadata
    posted_date: date | None = None
    job_embedding: list[float] | None = None  # 由 Retrieval 模块填充
```

### MatchResult（匹配结果）

```python
class MatchResult(BaseModel):
    """Retrieval 模块输出"""
    item_id: str  # 对应的 job_id 或 resume_id
    score: float = Field(ge=0.0, le=1.0, description="匹配分数")
    payload: dict = Field(default_factory=dict, description="原始 payload")
    match_type: Literal["resume_to_job", "job_to_resume", "skill_to_skill"]
```

### SimulationState（模拟状态 v2.0.0）

**权威定义**：`backend/simulation/state.py` → `backend/shared/types.py` 重导出。

```python
class AgentDecision(BaseModel):
    """单个 Agent 在单步模拟中的决策记录"""
    agent_name: str              # "candidate" | "hr" | "market" | "interview"
    action: str                  # 动作动词：apply | screen | adjust | assess | accept | reject
    params: dict                 # 动作参数
    reasoning: str               # 可解释性理由（必填）
    confidence: float = 0.5      # Agent 对该决策的置信度 [0, 1]
    timestamp: str               # ISO-8601

class SimulationState(BaseModel):
    """LangGraph StateGraph 全局状态 —— 所有 Agent 的唯一读写对象"""
    simulation_id: str
    strategy_name: str = "default"  # A | B | C 策略标签

    # 不可变实体
    candidate: StructuredResume
    job: StructuredJob

    # 当前位置
    current_step: Literal[
        "applied", "screened", "interview", "offer", "accepted", "rejected", "end"
    ] = "applied"
    step_count: int = 0          # 已执行的 Agent 动作次数
    max_steps: int = 20           # 安全上限

    # 审计轨迹（追加只读）
    decisions: list[AgentDecision] = []

    # 各阶段评分
    scores: dict[str, float] = {} # {"hr_screen": 0.8, "interview": 0.65, "final": 0.72}

    # 市场上下文
    market_adjustment: float = 1.0      # [0.5, 1.5] 供需修正
    competition_intensity: float = 0.5   # [0, 1] 竞争强度

    # 元数据
    timestamp: str               # ISO-8601 最后更新时间
```

### SimulationResult（模拟结果 v2.0.0）

```python
class SimulationResult(BaseModel):
    """一条模拟路径的最终产出 → Frontend 展示 / L3 Evolution 输入"""
    simulation_id: str
    strategy_name: str = "default"
    outcome: Literal["accepted", "rejected", "timeout"] = "timeout"

    final_state: SimulationState            # 最终状态快照
    success_probability: float              # [0, 1] 估算 P(offer)
    confidence_interval: tuple[float, float] # (下界, 上界)
    key_decisions: list[AgentDecision]      # 关键决策点（≤5条）
    time_to_offer: int = 0                  # applied → offer 步数
    path_history: list[SimulationState] = [] # 每步完整快照
    recommendation: str = ""                # 策略建议
```

---

## Retrieval Layer Contracts（v1.0.0）

> 本节定义 L1 Retrieval 模块的接口契约。实现由 @retrieval_agent 负责，契约由 @architect_agent 维护。
> 实现位于 `backend/retrieval/`，所有对外接口通过 `backend/shared/types.py` 的 `MatchResult` 与上下游通信。

---

### 1. EmbeddingService（嵌入服务接口）

**职责**：将 `StructuredResume` / `StructuredJob` 转化为归一化 dense vector。

**契约类型**：`typing.Protocol` —— 不规定实现（sentence-transformers / OpenAI / 其他），只规定 shape。

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class EmbeddingService(Protocol):
    """结构化文档 → dense vector。实现者负责模型加载与缓存。"""

    model_name: str        # "sentence-transformers/all-MiniLM-L6-v2"
    dim: int               # 384

    def encode_resume(self, resume: StructuredResume) -> list[float]:
        """将简历转为归一化向量，写入 resume.skill_embedding 后返回。"""
        ...

    def encode_job(self, job: StructuredJob) -> list[float]:
        """将岗位转为归一化向量，写入 job.job_embedding 后返回。"""
        ...

    def encode_batch(
        self, items: list[StructuredResume | StructuredJob], item_type: str
    ) -> list[list[float]]:
        """批量编码。item_type ∈ {"resume", "job"}。返回顺序与输入一致。"""
        ...
```

**文本拼接规则**（实现规范，非接口约束）：
- Resume → `summary + " ".join(skills) + project descriptions + experience descriptions`
- Job → `title + description + " ".join(required_skills) + " ".join(optional_skills) + level`

**性能约束**：
| 指标 | 目标 |
|------|------|
| 单条编码延迟 | < 100ms |
| 批量编码吞吐 | 32 条/批次 |
| 向量归一化 | 必须（保证 Cosine 语义正确） |

---

### 2. VectorStore Schema（Qdrant Collection 定义）

**职责**：存储向量并支持 Cosine 相似度检索。

**Collection 清单**：

#### `resumes`

```json
{
  "collection_name": "resumes",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  },
  "payload_schema": {
    "name":       {"type": "text"},
    "skills":     {"type": "keyword", "is_array": true},
    "summary":    {"type": "text"},
    "education_level": {"type": "keyword"}
  }
}
```

#### `jobs`

```json
{
  "collection_name": "jobs",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  },
  "payload_schema": {
    "title":            {"type": "text"},
    "company":          {"type": "text"},
    "required_skills":  {"type": "keyword", "is_array": true},
    "optional_skills":  {"type": "keyword", "is_array": true},
    "salary_range":     {"type": "integer", "is_array": true},
    "level":            {"type": "keyword"},
    "location":         {"type": "keyword"}
  }
}
```

#### `skills`（L3 阶段启用）

```json
{
  "collection_name": "skills",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  },
  "payload_schema": {
    "skill_name":  {"type": "keyword"},
    "category":    {"type": "keyword"},
    "market_value":{"type": "float"}
  }
}
```

**操作契约**：

```python
class VectorStore(Protocol):
    """向量存储 —— MVP 使用 Qdrant in-memory。"""

    # ── 写入 ──
    def upsert_resume(self, resume_id: str, vector: list[float], payload: dict) -> None: ...
    def upsert_job(self, job_id: str, vector: list[float], payload: dict) -> None: ...
    def upsert_batch(self, collection: str, ids: list[str], vectors: list[list[float]], payloads: list[dict]) -> None: ...

    # ── 检索 ──
    def search(
        self,
        collection: str,             # "resumes" | "jobs" | "skills"
        query_vector: list[float],   # dim=384 归一化向量
        top_k: int = 10,             # 返回数量
        score_threshold: float = 0.0,# 最低相似度阈值
        filters: dict | None = None, # Payload 过滤条件
    ) -> list[dict]:
        """返回 [{id, score, payload}, ...]。score ∈ [0.0, 1.0]。"""
        ...

    # ── 生命周期 ──
    def reset(self) -> None: ...
```

**过滤条件语法**（Qdrant 兼容）：

```json
{
  "must": [
    {"key": "level", "match": {"value": "高级"}},
    {"key": "required_skills", "match": {"any": ["Python", "FastAPI"]}}
  ]
}
```

---

### 3. Matcher（匹配编排器）—— 输入 / 输出契约

**职责**：编排 EmbeddingService + VectorStore，完成语义匹配全流程。这是 Retrieval 模块的唯一公开入口。

**契约类型**：具体类（非 Protocol），模块通过单例暴露。

```python
class Retriever:
    """语义匹配编排器 —— 上游 Parser / 下游 Simulation 的唯一依赖。"""

    # ── 索引（写入侧） ──

    async def index_resume(self, resume: StructuredResume) -> str:
        """
        Input:  StructuredResume（Parser 输出，skill_embedding 可选）
        Effect: 1) 若 skill_embedding 为空则调用 EmbeddingService.encode_resume()
                2) 写入 resumes collection
                3) 回填 resume.skill_embedding
        Output: resume_id: str
        """
        ...

    async def index_job(self, job: StructuredJob) -> str:
        """
        Input:  StructuredJob（Parser 输出，job_embedding 可选）
        Effect: 1) 若 job_embedding 为空则调用 EmbeddingService.encode_job()
                2) 写入 jobs collection
                3) 回填 job.job_embedding
        Output: job_id: str
        """
        ...

    async def index_jobs_batch(self, jobs: list[StructuredJob]) -> list[str]:
        """
        Input:  Job 列表
        Effect: 批量编码 + 批量写入
        Output: job_id 列表（顺序一致）
        """
        ...

    # ── 检索（读取侧） ──

    async def search_jobs(
        self,
        resume: StructuredResume,
        top_k: int = 10,
        score_threshold: float = 0.0,
        filters: dict | None = None,
    ) -> list[MatchResult]:
        """
        Input:  resume（已解析或已索引）
                top_k（返回数量）
                score_threshold（最低相似度）
                filters（Qdrant payload 过滤条件）
        Output: list[MatchResult]，按 score 降序
        Side-effect: 若 resume.skill_embedding 为空，自动编码
        """
        ...

    async def search_resumes(
        self,
        job: StructuredJob,
        top_k: int = 10,
        score_threshold: float = 0.0,
        filters: dict | None = None,
    ) -> list[MatchResult]:
        """
        Input:  job（已解析或已索引）
        Output: list[MatchResult]，match_type="job_to_resume"
        """
        ...

    # ── 生命周期 ──

    def reset(self) -> None:
        """清空所有 collection。仅用于测试或全量重建。"""
        ...
```

**Matcher 数据流**：

```
search_jobs(resume)
    │
    ├─ resume.skill_embedding?
    │   ├─ None → EmbeddingService.encode_resume(resume)
    │   └─ Some → 直接使用
    │
    ├─ VectorStore.search("jobs", query_vector, top_k, score_threshold, filters)
    │
    └─ raw hits → [MatchResult(item_id=h.id, score=h.score, payload=h.payload, match_type="resume_to_job")]
```

---

### 4. MatchResult（匹配结果）—— 唯一输出类型

**Pydantic 定义**（`backend/shared/types.py`，不可修改）：

```python
class MatchResult(BaseModel):
    """Retrieval 模块输出 → Simulation / Frontend 输入"""
    item_id: str                                          # 匹配到的 job_id 或 resume_id
    score: float = Field(ge=0.0, le=1.0)                  # Cosine 相似度
    payload: dict = Field(default_factory=dict)           # 匹配项的关键字段
    match_type: Literal[
        "resume_to_job",   # search_jobs() 的结果
        "job_to_resume",   # search_resumes() 的结果
        "skill_to_skill",  # 技能相似度查询（L3 阶段启用）
    ]
```

**Payload 内容规范**（约定优于配置）：

| match_type | payload 必须包含 | payload 可选 |
|-----------|-----------------|-------------|
| `resume_to_job` | `title`, `company`, `required_skills` | `optional_skills`, `salary_range`, `level`, `location` |
| `job_to_resume` | `name`, `skills` | `summary`, `education_level` |
| `skill_to_skill` | `skill_name`, `category` | `market_value` |

---

## HTTP API 契约

### POST /api/v1/parser/resume

**描述**：解析简历文件

**Request**：
```http
Content-Type: multipart/form-data

file: <PDF 或 Markdown 文件>
source_type: "pdf" | "markdown" | "text"
```

**Response**：
```json
{
  "resume_id": "res-001",
  "name": "张三",
  "skills": ["Python", "FastAPI"],
  "projects": [...],
  "education": [...],
  "experience": [...]
}
```

### POST /api/v1/retrieval/match

**描述**：为简历匹配岗位（`search_jobs`）

**Request**：
```json
{
  "resume_id": "res-001",
  "top_k": 10,
  "score_threshold": 0.3,
  "filters": {
    "must": [
      {"key": "level", "match": {"value": "高级"}},
      {"key": "location", "match": {"value": "上海"}}
    ]
  }
}
```

**Response**：
```json
{
  "matches": [
    {
      "item_id": "job-042",
      "score": 0.87,
      "payload": {
        "title": "后端工程师",
        "company": "ABC科技",
        "required_skills": ["Python", "FastAPI"],
        "optional_skills": ["GraphQL"],
        "salary_range": [300, 500],
        "level": "高级",
        "location": "上海"
      },
      "match_type": "resume_to_job"
    }
  ],
  "query_ms": 12
}
```

### POST /api/v1/retrieval/index/resume

**描述**：索引单份简历

**Request**：
```json
{
  "resume_id": "res-001"
}
```

**Response**：
```json
{
  "resume_id": "res-001",
  "indexed": true
}
```

### POST /api/v1/retrieval/index/job

**描述**：索引单个岗位

**Request**：
```json
{
  "job_id": "job-042"
}
```

**Response**：
```json
{
  "job_id": "job-042",
  "indexed": true
}
```

### POST /api/v1/retrieval/index/jobs/batch

**描述**：批量索引岗位

**Request**：
```json
{
  "job_ids": ["job-001", "job-002", "job-003"]
}
```

**Response**：
```json
{
  "indexed_count": 3,
  "job_ids": ["job-001", "job-002", "job-003"]
}
```

### POST /api/v1/retrieval/search/resumes

**描述**：反向搜索——给定岗位，检索最匹配候选人

**Request**：
```json
{
  "job_id": "job-042",
  "top_k": 10,
  "score_threshold": 0.3,
  "filters": {
    "must": [
      {"key": "skills", "match": {"any": ["Python", "Kubernetes"]}}
    ]
  }
}
```

**Response**：
```json
{
  "matches": [
    {
      "item_id": "res-001",
      "score": 0.87,
      "payload": {
        "name": "张三",
        "skills": ["Python", "FastAPI", "Kubernetes"]
      },
      "match_type": "job_to_resume"
    }
  ],
  "query_ms": 8
}
```

### POST /api/v1/simulation/run

**描述**：运行单路径模拟。返回 FinalT004Schema — ProductView（UI 渲染） + Explanation（可解释分析） + 原始数据。

**Request**：
```json
{
  "resume_id": "res-001",
  "job_id": "job-042",
  "strategy": "balanced"
}
```

**Response**（FinalT004Schema v1.0.0）：
```json
{
  "simulation_id": "sim-789abc",
  "strategy_name": "balanced",
  "outcome": "accepted",

  "summary": {
    "headline": "Offer accepted after 3 steps",
    "candidate_name": "Alice Wang",
    "job_title": "Senior Backend Engineer",
    "company": "ACME Corp",
    "badge": "success",
    "stats": {
      "success_probability": 0.8,
      "time_to_offer_steps": 3,
      "total_reward": 0.99
    }
  },

  "match_score": {
    "overall": 100,
    "breakdown": {"skill_match": 100, "experience_fit": 97, "keyword_overlap": 100},
    "gauge": {"value": 100, "color": "green", "label": "Strong"}
  },

  "timeline": {
    "events": [
      {
        "step": 0, "phase": "applied", "actor": "candidate",
        "action_label": "Applied to position",
        "reasoning": "Skill match 100% exceeds threshold 60%.",
        "score": null, "confidence": 0.65, "timestamp": "2025-01-15T..."
      }
    ],
    "total_steps": 3
  },

  "skill_gap_chart": {
    "matched": [{"name": "Python", "value": 100, "category": "required"}],
    "missing": [{"name": "Terraform", "value": 40, "category": "optional"}],
    "title": "Skill Match: 86%",
    "match_ratio": 0.86
  },

  "recommendation_cards": [
    {
      "priority": 1, "type": "success",
      "title": "Proceed with Application",
      "description": "The 'balanced' strategy led to an offer.",
      "action_label": "Apply now"
    }
  ],

  "decision_path": {
    "title": "Successful 'balanced' strategy — offer accepted",
    "total_actions": 4,
    "steps": [
      {"order": 1, "agent": "candidate", "action": "apply",
       "summary": "Candidate decided to apply for the position.",
       "reasoning": "...", "confidence": 0.65}
    ]
  },

  "hr_reasoning": {
    "evaluation": "HR screen: PASS. Score=0.97...",
    "score": 0.969, "verdict": "passed",
    "details": ["Skill match: 100%", "Experience fit: 88%", "Keyword overlap: 100%"],
    "rejection_reasons": []
  },

  "candidate_actions": {
    "strategy": "balanced",
    "strategy_explanation": "Candidate balanced preparation with timely applications.",
    "total_actions": 3,
    "actions": [
      {"action": "apply", "confidence": 0.65, "reasoning": "...", "gap_skills": [], "match_score": 1.0}
    ]
  },

  "failure_points": [],

  "confidence_score": {
    "overall": 0.88,
    "factors": {"data_richness": 1.0, "gate_coverage": 1.0, "outcome_clarity": 1.0},
    "interpretation": "High — explanation is well-supported by simulation data."
  },

  "result": {"...": "SimulationResult.model_dump()"},
  "metrics": {"offer_probability": 1.0, "skill_gap_score": 1.0, "total_reward": 0.99}
}
```

**Schema 结构**：

```
FinalT004Schema {
    simulation_id, strategy_name, outcome          ← identity

    // ProductView (UI rendering) — T-004-A
    summary, match_score, timeline,
    skill_gap_chart, recommendation_cards

    // Explanation (interpretability) — T-004-B
    decision_path, hr_reasoning, candidate_actions,
    failure_points, confidence_score

    // Backward-compatible raw data
    result: SimulationResult, metrics: dict
}
```

### POST /api/v1/simulation/compare

**描述**：多策略对比模拟

**Request**：
```json
{
  "resume_id": "res-001",
  "job_id": "job-042",
  "strategies": ["aggressive", "conservative", "balanced"]
}
```

**Response**：
```json
{
  "comparison": [
    {
      "strategy_name": "aggressive",
      "outcome": "accepted",
      "success_probability": 0.65,
      "time_to_offer": 3,
      "total_reward": 0.72
    },
    {
      "strategy_name": "conservative",
      "outcome": "accepted",
      "success_probability": 0.8,
      "time_to_offer": 5,
      "total_reward": 0.99
    },
    {
      "strategy_name": "balanced",
      "outcome": "accepted",
      "success_probability": 0.8,
      "time_to_offer": 3,
      "total_reward": 0.99
    }
  ]
}
```

---

## 变更日志

| 版本 | 日期 | 变更内容 | 影响模块 |
|------|------|---------|---------|
| 1.0.0 | 2025-XX-XX | 初始版本 | 全部 |
| 1.1.0 | 2025-XX-XX | 新增 Retrieval Layer Contracts（EmbeddingService / VectorStore / Retriever 接口 + Qdrant schema） | Retrieval, Parser（索引依赖）, Simulation（匹配结果消费） |
| 1.2.0 | 2025-XX-XX | StructuredJob 字段重构：`skills_required`→`required_skills`，新增 `optional_skills`，`salary_min/max`→`salary_range` | Parser, Retrieval, Simulation |
| 2.0.0 | 2025-XX-XX | FinalT004Schema：合并 ProductView + Explanation → 统一 simulation/run 响应。新增 10 个 UI/分析 section，保留 result/metrics 向后兼容。 | Simulation, Frontend |
