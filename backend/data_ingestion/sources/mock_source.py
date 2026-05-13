"""MockJobSource — development/test adapter implementing the SourceAdapter Protocol.

Provides 15 representative job postings across different domains (frontend,
backend, data, ML) so the pipeline can function end-to-end without real scrapers.
"""

from __future__ import annotations

from backend.data_ingestion.schemas import RawJobPosting

MOCK_JOBS: list[dict] = [
    {
        "source": "mock",
        "raw_id": "m001",
        "title": "高级前端工程师",
        "company": "字节跳动",
        "location": "北京",
        "salary_text": "40K-70K/月",
        "skills_text": "React, TypeScript, Webpack, Node.js, CSS",
        "description": "负责抖音电商前端架构设计与核心模块开发",
        "level": "高级",
    },
    {
        "source": "mock",
        "raw_id": "m002",
        "title": "Python 后端开发",
        "company": "阿里巴巴",
        "location": "杭州",
        "salary_text": "35K-60K/月",
        "skills_text": "Python, Django, MySQL, Redis, Docker",
        "description": "负责电商中台服务开发与性能优化",
        "level": "中级",
    },
    {
        "source": "mock",
        "raw_id": "m003",
        "title": "机器学习工程师",
        "company": "腾讯",
        "location": "深圳",
        "salary_text": "50K-90K/月",
        "skills_text": "Python, PyTorch, TensorFlow, CUDA, MLOps",
        "description": "负责大模型训练与推理优化",
        "level": "高级",
    },
    {
        "source": "mock",
        "raw_id": "m004",
        "title": "数据分析师",
        "company": "美团",
        "location": "北京",
        "salary_text": "25K-45K/月",
        "skills_text": "SQL, Python, Tableau, Excel, 统计学",
        "description": "负责业务数据分析与可视化报表",
        "level": "初级",
    },
    {
        "source": "mock",
        "raw_id": "m005",
        "title": "DevOps 工程师",
        "company": "华为",
        "location": "深圳",
        "salary_text": "35K-55K/月",
        "skills_text": "Kubernetes, Docker, Jenkins, Terraform, AWS",
        "description": "负责 CI/CD 流水线与容器化部署",
        "level": "中级",
    },
    {
        "source": "mock",
        "raw_id": "m006",
        "title": "全栈工程师",
        "company": "小红书",
        "location": "上海",
        "salary_text": "35K-60K/月",
        "skills_text": "React, Go, PostgreSQL, Redis, TypeScript",
        "description": "负责社区业务全栈开发",
        "level": "中级",
    },
    {
        "source": "mock",
        "raw_id": "m007",
        "title": "后端架构师",
        "company": "百度",
        "location": "北京",
        "salary_text": "60K-100K/月",
        "skills_text": "Java, Spring, Microservices, Kafka, Flink",
        "description": "负责搜索中台架构设计与技术规划",
        "level": "架构师",
    },
    {
        "source": "mock",
        "raw_id": "m008",
        "title": "iOS 开发工程师",
        "company": "快手",
        "location": "北京",
        "salary_text": "30K-50K/月",
        "skills_text": "Swift, Objective-C, UIKit, SwiftUI, CI/CD",
        "description": "负责短视频客户端功能开发",
        "level": "中级",
    },
    {
        "source": "mock",
        "raw_id": "m009",
        "title": "NLP 研究员",
        "company": "商汤科技",
        "location": "上海",
        "salary_text": "45K-80K/月",
        "skills_text": "Python, Transformers, BERT, GPT, 语言学",
        "description": "负责自然语言处理前沿研究",
        "level": "高级",
    },
    {
        "source": "mock",
        "raw_id": "m010",
        "title": "测试开发工程师",
        "company": "京东",
        "location": "北京",
        "salary_text": "30K-50K/月",
        "skills_text": "Python, Selenium, JMeter, Jenkins, Appium",
        "description": "负责电商系统自动化测试框架搭建",
        "level": "中级",
    },
    {
        "source": "mock",
        "raw_id": "m011",
        "title": "Golang 后端开发",
        "company": "滴滴",
        "location": "北京",
        "salary_text": "35K-55K/月",
        "skills_text": "Go, gRPC, MySQL, Redis, ElasticSearch",
        "description": "负责出行调度系统开发",
        "level": "中级",
    },
    {
        "source": "mock",
        "raw_id": "m012",
        "title": "技术总监",
        "company": "字节跳动",
        "location": "北京",
        "salary_text": "80K-120K/月",
        "skills_text": "架构设计, 团队管理, 技术规划, 跨部门协作",
        "description": "负责抖音电商技术团队管理与技术战略",
        "level": "总监",
    },
    {
        "source": "mock",
        "raw_id": "m013",
        "title": "初级前端开发",
        "company": "网易",
        "location": "广州",
        "salary_text": "15K-25K/月",
        "skills_text": "HTML, CSS, JavaScript, React, Git",
        "description": "负责内部管理系统前端开发",
        "level": "初级",
    },
    {
        "source": "mock",
        "raw_id": "m014",
        "title": "数据工程师",
        "company": "蚂蚁集团",
        "location": "杭州",
        "salary_text": "40K-70K/月",
        "skills_text": "Spark, Flink, Kafka, Hive, Scala, Python",
        "description": "负责实时数据管道搭建与数据治理",
        "level": "高级",
    },
    {
        "source": "mock",
        "raw_id": "m015",
        "title": "安全工程师",
        "company": "奇安信",
        "location": "北京",
        "salary_text": "30K-50K/月",
        "skills_text": "网络安全, 渗透测试, 入侵检测, SIEM, Python",
        "description": "负责企业安全防护与漏洞挖掘",
        "level": "中级",
    },
]


class MockJobSource:
    """Development/test adapter providing pre-defined sample jobs.

    Implements the SourceAdapter Protocol (duck-typed — no explicit inheritance).
    """

    source_name: str = "mock"

    async def fetch(self) -> list[dict]:
        """Return all mock job postings as raw dicts."""
        return [dict(j) for j in MOCK_JOBS]

    def normalize(self, raw: dict) -> dict:
        """Convert one raw dict into UnifiedJob-compatible fields."""
        return {
            "source": raw.get("source", "mock"),
            "raw_id": raw["raw_id"],
            "title": raw.get("title", ""),
            "company": raw.get("company", ""),
            "location": raw.get("location", ""),
            "salary_text": raw.get("salary_text", ""),
            "skills_text": raw.get("skills_text", ""),
            "description": raw.get("description", ""),
            "level": raw.get("level", ""),
        }

    def __repr__(self) -> str:
        return f"MockJobSource(n={len(MOCK_JOBS)})"
