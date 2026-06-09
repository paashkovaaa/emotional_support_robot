import client from './client';

/* ── Types specific to chat API ── */

export interface ConversationCreate {
  title?: string | null;
  chat_type?: 'text' | 'voice';
}

export interface ConversationDetail {
  id: string;
  user_id: string;
  title: string | null;
  chat_type: 'text' | 'voice';
  status: 'active' | 'ended';
  started_at: string;
  ended_at: string | null;
  summary: string | null;
  message_count: number;
}

export interface ConversationListItem {
  id: string;
  title: string | null;
  chat_type: 'text' | 'voice';
  status: 'active' | 'ended';
  started_at: string;
  ended_at: string | null;
  message_count: number;
  last_message_preview: string | null;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender: 'user' | 'bot';
  content: string;
  sent_at: string;
  crisis_level: 'none' | 'low' | 'medium' | 'high' | 'critical';
  is_crisis: boolean;
}

export interface MessagesListResponse {
  messages: ChatMessage[];
  total: number;
  conversation_id: string;
}

/* ── Conversations ── */

export async function createConversation(data?: ConversationCreate): Promise<ConversationDetail> {
  const res = await client.post<ConversationDetail>('/chat/conversations', data ?? {});
  return res.data;
}

export async function getConversations(
  limit = 50,
  offset = 0,
): Promise<ConversationListItem[]> {
  const res = await client.get<ConversationListItem[]>('/chat/conversations', {
    params: { limit, offset },
  });
  return res.data;
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const res = await client.get<ConversationDetail>(`/chat/conversations/${id}`);
  return res.data;
}

export async function updateConversation(
  id: string,
  data: { title?: string | null },
): Promise<ConversationDetail> {
  const res = await client.patch<ConversationDetail>(`/chat/conversations/${id}`, data);
  return res.data;
}

export async function endConversation(id: string): Promise<ConversationDetail> {
  const res = await client.post<ConversationDetail>(`/chat/conversations/${id}/end`);
  return res.data;
}

export async function deleteConversation(id: string): Promise<void> {
  await client.delete(`/chat/conversations/${id}`);
}

/* ── Messages ── */

export async function getMessages(
  conversationId: string,
  limit = 100,
  offset = 0,
): Promise<MessagesListResponse> {
  const res = await client.get<MessagesListResponse>(
    `/chat/conversations/${conversationId}/messages`,
    { params: { limit, offset } },
  );
  return res.data;
}

export async function sendMessage(
  conversationId: string,
  content: string,
): Promise<ChatMessage> {
  const res = await client.post<ChatMessage>(
    `/chat/conversations/${conversationId}/messages`,
    { content },
  );
  return res.data;
}

