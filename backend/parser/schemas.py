"""Parser-internal schemas — skill synonyms, section patterns, parsing config."""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Skill name normalization map
# ---------------------------------------------------------------------------
SKILL_SYNONYMS: dict[str, str] = {
    "react.js": "React",
    "reactjs": "React",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "python3": "Python",
    "py": "Python",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "golang": "Go",
    "go-lang": "Go",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "pg": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "docker": "Docker",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "large language model": "LLM",
    "llm": "LLM",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "redis": "Redis",
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "graphql": "GraphQL",
    "gql": "GraphQL",
    "rest": "REST",
    "restful": "REST",
    "grpc": "gRPC",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "git": "Git",
    "linux": "Linux",
    "unix": "Unix",
}

# ---------------------------------------------------------------------------
# Rule-based fallback patterns
# ---------------------------------------------------------------------------
SECTION_PATTERNS: dict[str, re.Pattern] = {
    "skills": re.compile(
        r"(?:技能|skills?|技术栈|tech[_\s]?stack|proficienc(?:y|ies))[\s:：]*(.+?)(?:\n\n|\n(?:项目|工作|教育|经历|experience|project|education|$))",
        re.IGNORECASE | re.DOTALL,
    ),
    "name": re.compile(
        r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})|([一-鿿]{2,4})",
        re.MULTILINE,
    ),
    "email": re.compile(
        r"[\w.\-+]+@[\w.\-]+\.[a-z]{2,}",
        re.IGNORECASE,
    ),
    "phone": re.compile(
        r"(?:\+86[\s-]?)?1[3-9]\d[\s-]?\d{4}[\s-]?\d{4}",
    ),
}

# ---------------------------------------------------------------------------
# LLM prompt template
# ---------------------------------------------------------------------------
RESUME_PARSE_PROMPT = """Extract structured information from this resume text. Output ONLY valid JSON, no markdown, no explanation.

Resume text:
{resume_text}

Output format:
{{
  "name": "full name",
  "email": "email or null",
  "phone": "phone or null",
  "summary": "short professional summary",
  "skills": ["normalized skill name", ...],
  "projects": [
    {{"name": "project name", "description": "what it does", "tech_stack": ["tech", ...], "start_date": "YYYY-MM-DD or null", "end_date": "YYYY-MM-DD or null"}}
  ],
  "education": [
    {{"school": "school name", "degree": "本科/硕士/博士/其他", "major": "major", "graduation_year": 2024 or null}}
  ],
  "experience": [
    {{"company": "company", "title": "job title", "description": "what you did", "tech_stack": ["tech", ...], "start_date": "YYYY-MM-DD or null", "end_date": "YYYY-MM-DD or null"}}
  ],
  "certifications": ["cert name", ...]
}}

Rules:
- Normalize all skill names: "React.js" → "React", "NodeJS" → "Node.js", "k8s" → "Kubernetes"
- If a field is missing, use [] for lists, "" for strings, null for optional
- Dates should be ISO format "YYYY-MM-DD"
- education degree must be one of: "本科", "硕士", "博士", "其他"
- JSON only, no markdown```, no prefix text"""


def normalize_skill(raw: str) -> str:
    """Normalize a single skill name. Returns the canonical form."""
    key = raw.strip().lower()
    # Direct match
    if key in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[key]
    # Title-case as fallback
    return raw.strip().title()


def normalize_skills(raw_skills: list[str]) -> list[str]:
    """Normalize and deduplicate a list of skill strings."""
    seen: set[str] = set()
    result: list[str] = []
    for s in raw_skills:
        normalized = normalize_skill(s)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
