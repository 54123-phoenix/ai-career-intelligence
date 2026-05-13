/** Chat API — AI 职业助手对话（SSE 流式） */

import { apiStream } from './client';

export interface ChatMessageRequest {
  message: string;
  conversation_id?: string;
  context?: {
    user_profile?: Record<string, unknown>;
    recent_analysis?: Record<string, unknown>;
  };
}

export async function streamChatMessage(
  params: ChatMessageRequest
): Promise<ReadableStreamDefaultReader<Uint8Array>> {
  return apiStream('/chat/message', params);
}
