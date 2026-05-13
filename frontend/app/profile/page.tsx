"use client";

import { useState } from "react";

export default function ProfilePage() {
  const [profile, setProfile] = useState({
    name: "演示用户",
    email: "demo@example.com",
    experience_years: 3,
    education_level: "本科",
    skills: ["Python", "FastAPI", "PostgreSQL"],
    career_goals: ["高级后端工程师", "技术专家"],
    preferred_locations: ["北京", "上海"],
  });

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">用户中心</h1>

      <div className="space-y-6">
        <section className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">基本信息</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">姓名</label>
              <input
                className="w-full rounded-lg border px-3 py-2 text-sm"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">邮箱</label>
              <input
                className="w-full rounded-lg border px-3 py-2 text-sm"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">工作经验（年）</label>
              <input
                type="number"
                className="w-full rounded-lg border px-3 py-2 text-sm"
                value={profile.experience_years}
                onChange={(e) => setProfile({ ...profile, experience_years: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">学历</label>
              <select
                className="w-full rounded-lg border px-3 py-2 text-sm"
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

        <section className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">职业兴趣</h2>
          <div>
            <label className="block text-xs text-gray-500 mb-1">技能标签（逗号分隔）</label>
            <input
              className="w-full rounded-lg border px-3 py-2 text-sm"
              value={profile.skills.join(", ")}
              onChange={(e) => setProfile({ ...profile, skills: e.target.value.split(",").map((s) => s.trim()) })}
            />
          </div>
          <div className="mt-4">
            <label className="block text-xs text-gray-500 mb-1">职业目标（逗号分隔）</label>
            <input
              className="w-full rounded-lg border px-3 py-2 text-sm"
              value={profile.career_goals.join(", ")}
              onChange={(e) => setProfile({ ...profile, career_goals: e.target.value.split(",").map((s) => s.trim()) })}
            />
          </div>
        </section>

        <section className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">操作记录</h2>
          <div className="text-sm text-gray-500">
            <p>• 2025-05-10 完成职业分析 — 高级后端工程师路径</p>
            <p>• 2025-05-09 运行职业模拟 — 均衡策略，成功率 78%</p>
            <p>• 2025-05-08 更新技能标签</p>
          </div>
        </section>
      </div>
    </main>
  );
}
