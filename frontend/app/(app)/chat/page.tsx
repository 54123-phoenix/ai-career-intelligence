"use client";

import { useState, useRef } from "react";
import { streamChatMessage } from "@/lib/api/chat";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "您好！我是您的职业智能助手。可以为您解答职业发展、技能提升、岗位匹配等方面的问题。",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const abortRef = useRef<AbortController | null>(null);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    // Placeholder for assistant response (will be streamed)
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const reader = await streamChatMessage({
        message: userMsg,
        conversation_id: conversationId,
      });

      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { role: "assistant", content: fullText };
          return next;
        });
      }

      // If backend returns a conversation_id in a separate header or
      // final frame, we would extract it here. For now we keep the current one.
    } catch (e) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: `抱歉，服务暂时不可用。${e instanceof Error ? e.message : ""}`,
        };
        return next;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
        AI 职业助手
      </h1>
      <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
        提供职业建议问答、策略讨论与路径规划支持
      </p>

      <div className="flex h-[60vh] flex-col rounded-xl border bg-white shadow-sm dark:border-gray-700 dark:bg-slate-900">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-gray-100"
                }`}
              >
                {msg.content || (
                  <span className="inline-flex gap-1">
                    <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400" />
                    <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
                    <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-2 border-t p-4 dark:border-gray-700">
          <input
            className="flex-1 rounded-lg border px-3 py-2 text-sm dark:border-gray-600 dark:bg-slate-800 dark:text-white"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="输入您的问题..."
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </div>
    </main>
  );
}
