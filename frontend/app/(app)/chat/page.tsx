'use client';

import { useState, useRef, useCallback, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { streamChatMessage } from '@/lib/api/chat';
import 'highlight.js/styles/github-dark.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const MarkdownContent = memo(function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
        ul: ({ children }) => <ul className="mb-2 list-disc pl-4 last:mb-0">{children}</ul>,
        ol: ({ children }) => <ol className="mb-2 list-decimal pl-4 last:mb-0">{children}</ol>,
        li: ({ children }) => <li className="mb-0.5">{children}</li>,
        code({ className, children, ...props }) {
          const isInline = !className?.includes('language-');
          return isInline ? (
            <code className="rounded bg-slate-700 px-1 py-0.5 text-xs text-slate-100" {...props}>
              {children}
            </code>
          ) : (
            <pre className="my-2 overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs">
              <code className={className} {...props}>
                {children}
              </code>
            </pre>
          );
        },
        h1: ({ children }) => <h1 className="mb-2 text-base font-bold">{children}</h1>,
        h2: ({ children }) => <h2 className="mb-2 text-sm font-bold">{children}</h2>,
        h3: ({ children }) => <h3 className="mb-1 text-sm font-semibold">{children}</h3>,
        blockquote: ({ children }) => (
          <blockquote className="mb-2 border-l-2 border-indigo-400 pl-3 text-slate-300 italic">
            {children}
          </blockquote>
        ),
        a: ({ children, href }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 underline"
          >
            {children}
          </a>
        ),
        table: ({ children }) => (
          <table className="mb-2 w-full border-collapse text-xs">{children}</table>
        ),
        th: ({ children }) => (
          <th className="border border-slate-600 bg-slate-800 px-2 py-1 text-left font-semibold">
            {children}
          </th>
        ),
        td: ({ children }) => <td className="border border-slate-600 px-2 py-1">{children}</td>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
});

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '您好！我是您的职业智能助手。可以为您解答职业发展、技能提升、岗位匹配等方面的问题。',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const abortRef = useRef<AbortController | null>(null);

  const handleSend = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    try {
      const reader = await streamChatMessage({
        message: userMsg,
        conversation_id: conversationId,
      });

      const decoder = new TextDecoder();
      let fullText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { role: 'assistant', content: fullText };
          return next;
        });
      }
    } catch (e) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'assistant',
          content: `抱歉，服务暂时不可用。${e instanceof Error ? e.message : ''}`,
        };
        return next;
      });
    } finally {
      setLoading(false);
    }
  }, [input, loading, conversationId]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">AI 职业助手</h1>
      <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
        提供职业建议问答、策略讨论与路径规划支持
      </p>

      <div className="flex h-[60vh] flex-col rounded-xl border bg-white shadow-sm dark:border-gray-700 dark:bg-slate-900">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-gray-100'
                }`}
              >
                {msg.content ? (
                  msg.role === 'assistant' ? (
                    <MarkdownContent content={msg.content} />
                  ) : (
                    <p className="leading-relaxed">{msg.content}</p>
                  )
                ) : (
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
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
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
