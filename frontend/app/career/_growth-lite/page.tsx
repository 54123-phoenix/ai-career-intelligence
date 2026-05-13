"use client";

import { useState } from "react";
import type { T010PipelineOutput } from "@/types/t010";
import { runT010Pipeline, getT010UpgradeInterfaces } from "@/lib/t010-api";
import {
  StrategyComparison,
  CareerPathGraph,
  SimulationFeedback,
  CareerPlanTimeline,
} from "@/components/career";

const SAMPLE_DATASET: Record<string, unknown>[] = [
  {
    job_title: "Senior Backend Engineer",
    required_skills: ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
    optional_skills: ["AWS", "Terraform", "GraphQL"],
    growth_path: ["Junior Backend", "Backend Engineer", "Senior Backend", "Staff Engineer"],
    level: "高级", salary_range: [400, 650], location: "北京", industry: "互联网", source: "sample",
  },
  {
    job_title: "Machine Learning Engineer",
    required_skills: ["Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning"],
    optional_skills: ["Kubernetes", "MLOps", "NLP"],
    growth_path: ["Data Analyst", "ML Engineer", "Senior MLE", "ML Architect"],
    level: "高级", salary_range: [500, 800], location: "上海", industry: "人工智能", source: "sample",
  },
  {
    job_title: "Frontend Tech Lead",
    required_skills: ["TypeScript", "React", "Next.js", "CSS", "System Design"],
    optional_skills: ["GraphQL", "Webpack", "React Native"],
    growth_path: ["Frontend Developer", "Senior Frontend", "Tech Lead", "Frontend Architect"],
    level: "高级", salary_range: [450, 700], location: "深圳", industry: "互联网", source: "sample",
  },
];

export default function CareerGrowthLitePage() {
  const [data, setData] = useState<T010PipelineOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [upgradeInterfaces, setUpgradeInterfaces] = useState<Record<string, { agent: string; core_capability: string; upgrade_hooks: string[]; upgrade_notes: string }> | null>(null);

  const [userInput, setUserInput] = useState(
    "目标成为高级后端工程师，掌握 Python、FastAPI、PostgreSQL，有3年经验，本科，期望在北京工作"
  );
  const [privacyLevel, setPrivacyLevel] = useState("basic");

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const result = await runT010Pipeline({
        user_id: "demo-user-lite",
        user_input: userInput,
        career_dataset: SAMPLE_DATASET,
        privacy_level: privacyLevel,
      });
      setData(result.data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadUpgrades() {
    try {
      const interfaces = await getT010UpgradeInterfaces();
      setUpgradeInterfaces(interfaces.agents);
      setShowUpgrade(true);
    } catch (e) {
      console.error("Failed to load upgrade interfaces:", e);
    }
  }

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "strategies", label: "Strategies" },
    { key: "plan", label: "Plan" },
    { key: "path", label: "Path" },
    { key: "simulation", label: "Simulation" },
  ];

  return (
    <main>test</main>
  );
}
