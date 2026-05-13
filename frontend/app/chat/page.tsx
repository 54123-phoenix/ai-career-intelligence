"use client";

import { useState } from "react";

export default function ChatPage() {
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([
    { role: "assistant", content: "您好！我是您的职业智能助手。可以为您解答职业发展、技能提升、岗位匹配等方面的问题。" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    // Placeholder: integrate with backend AI assistant API
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `收到您的问题："${userMsg}"。（此处将接入 AI 职业建议对话接口）` },
      ]);
      setLoading(false);
    }, 1200);
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">AI 职业助手</h1>
      <p className="mb-4 text-sm text-gray-500">
        提供职业建议问答、策略讨论与路径规划支持
      </p>

      <div className="rounded-xl border bg-white shadow-sm flex flex-col h-[60vh]">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg px-4 py-2 text-sm text-gray-500">
                思考中...
              </div>
            </div>
          )}
        </div>

        <div className="border-t p-4 flex gap-2">
          <input
            className="flex-1 rounded-lg border px-3 py-2 text-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="输入您的问题..."
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </div>
    </main>
  );
}
