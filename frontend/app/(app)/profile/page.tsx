"use client";

import { useState, useEffect } from "react";
import { getCurrentUser, updateUserProfile, getUserHistory, type UserHistoryItem } from "@/lib/api/user";
import type { UserProfile } from "@/types/user";

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [history, setHistory] = useState<UserHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [user, hist] = await Promise.all([
          getCurrentUser(),
          getUserHistory({ limit: 10 }),
        ]);
        setProfile(user);
        setHistory(hist.items);
      } catch {
        // Fallback to demo data if API not ready
        setProfile({
          user_id: "demo-user",
          email: "demo@example.com",
          name: "演示用户",
          role: "user",
          created_at: new Date().toISOString(),
          career_goals: ["高级后端工程师", "技术专家"],
          preferred_industries: ["互联网", "人工智能"],
          preferred_locations: ["北京", "上海"],
          salary_expectation: [300, 600],
          privacy_level: "basic",
          skills: ["Python", "FastAPI", "PostgreSQL"],
          experience_years: 3,
          education_level: "本科",
        });
        setHistory([
          { id: "1", type: "analysis", title: "职业分析", description: "高级后端工程师路径", created_at: "2025-05-10T10:00:00Z" },
          { id: "2", type: "simulation", title: "职业模拟", description: "均衡策略，成功率 78%", created_at: "2025-05-09T14:30:00Z" },
          { id: "3", type: "profile_update", title: "更新资料", description: "修改技能标签", created_at: "2025-05-08T09:15:00Z" },
        ]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    setMessage(null);
    try {
      const updated = await updateUserProfile({
        name: profile.name,
        career_goals: profile.career_goals,
        preferred_locations: profile.preferred_locations,
        skills: profile.skills,
        experience_years: profile.experience_years,
        education_level: profile.education_level,
      });
      setProfile(updated);
      setMessage("保存成功");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-8">
        <div className="rounded-xl border bg-white p-12 text-center text-gray-400 dark:border-gray-700 dark:bg-slate-900">
          加载中...
        </div>
      </main>
    );
  }

  if (!profile) return null;

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">用户中心</h1>
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? "保存中..." : "保存修改"}
        </button>
      </div>

      {message && (
        <div
          className={`mb-4 rounded-lg p-3 text-sm ${
            message === "保存成功"
              ? "border border-green-200 bg-green-50 text-green-800 dark:border-green-900/30 dark:bg-green-950/30 dark:text-green-300"
              : "border border-red-200 bg-red-50 text-red-800 dark:border-red-900/30 dark:bg-red-950/30 dark:text-red-300"
          }`}
        >
          {message}
        </div>
      )}

      <div className="space-y-6">
        <section className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">基本信息</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">姓名</label>
              <input
                className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">邮箱</label>
              <input
                className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
                value={profile.email}
                readOnly
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">
                工作经验（年）
              </label>
              <input
                type="number"
                className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
                value={profile.experience_years}
                onChange={(e) =>
                  setProfile({ ...profile, experience_years: Number(e.target.value) })
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">学历</label>
              <select
                className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
                value={profile.education_level}
                onChange={(e) => setProfile({ ...profile, education_level: e.target.value })}
              >
                <option>本科</option>
                <option>硕士</option>
                <option>博士</option>
                <option>其他</option>
              </select>
            </div>
          </div>
        </section>

        <section className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">职业兴趣</h2>
          <div>
            <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">
              技能标签（逗号分隔）
            </label>
            <input
              className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
              value={profile.skills.join(", ")}
              onChange={(e) =>
                setProfile({ ...profile, skills: e.target.value.split(",").map((s) => s.trim()) })
              }
            />
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">
              职业目标（逗号分隔）
            </label>
            <input
              className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
              value={profile.career_goals.join(", ")}
              onChange={(e) =>
                setProfile({ ...profile, career_goals: e.target.value.split(",").map((s) => s.trim()) })
              }
            />
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">
              期望地点（逗号分隔）
            </label>
            <input
              className="w-full rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
              value={profile.preferred_locations.join(", ")}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  preferred_locations: e.target.value.split(",").map((s) => s.trim()),
                })
              }
            />
          </div>
        </section>

        <section className="rounded-xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">操作记录</h2>
          <div className="space-y-2 text-sm">
            {history.length === 0 && (
              <p className="text-gray-400 dark:text-gray-500">暂无记录</p>
            )}
            {history.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-lg border px-3 py-2 dark:border-gray-700"
              >
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">{item.title}</span>
                  <span className="mx-2 text-gray-300">·</span>
                  <span className="text-gray-500 dark:text-gray-400">{item.description}</span>
                </div>
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {new Date(item.created_at).toLocaleDateString("zh-CN")}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
