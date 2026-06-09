import { create } from 'zustand';
import * as chatApi from '../api/chat';
import type { ConversationListItem, ChatMessage, ConversationDetail } from '../api/chat';

interface ChatState {
  /** Список розмов */
  conversations: ConversationListItem[];
  /** Поточна активна розмова */
  activeConversation: ConversationDetail | null;
  /** Повідомлення поточної розмови */
  messages: ChatMessage[];
  /** Стан */
  loading: boolean;
  messagesLoading: boolean;
  sending: boolean;
  /** Бот друкує */
  botTyping: boolean;
  /** Поточний стримінговий текст відповіді бота (chunk by chunk) */
  streamingContent: string;
  error: string | null;

  // ── Дії ──
  fetchConversations: () => Promise<void>;
  createConversation: (title?: string) => Promise<ConversationDetail>;
  selectConversation: (id: string) => Promise<void>;
  endConversation: (id: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<ChatMessage>;
  addMessage: (msg: ChatMessage) => void;
  /** Додати оптимістичне повідомлення користувача (без звʼязку з API) */
  addOptimisticUserMessage: (content: string, conversationId: string) => string;
  setBotTyping: (typing: boolean) => void;
  /** Додати chunk до поточної стримінгової відповіді */
  appendStreamChunk: (chunk: string) => void;
  /** Завершити стримінг і очистити буфер */
  finalizeStream: () => void;
  clearActiveConversation: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversation: null,
  messages: [],
  loading: false,
  messagesLoading: false,
  sending: false,
  botTyping: false,
  streamingContent: '',
  error: null,

  fetchConversations: async () => {
    set({ loading: true, error: null });
    try {
      const conversations = await chatApi.getConversations();
      set({ conversations, loading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Не вдалося завантажити розмови';
      set({ error: message, loading: false });
    }
  },

  createConversation: async (title) => {
    const conv = await chatApi.createConversation({ title });
    set((s) => ({
      conversations: [
        {
          id: conv.id,
          title: conv.title,
          chat_type: conv.chat_type,
          status: conv.status,
          started_at: conv.started_at,
          ended_at: conv.ended_at,
          message_count: 0,
          last_message_preview: null,
        },
        ...s.conversations,
      ],
      activeConversation: conv,
      messages: [],
    }));
    return conv;
  },

  selectConversation: async (id) => {
    set({ messagesLoading: true, error: null });
    try {
      const [conv, msgResponse] = await Promise.all([
        chatApi.getConversation(id),
        chatApi.getMessages(id),
      ]);
      set({
        activeConversation: conv,
        messages: msgResponse.messages,
        messagesLoading: false,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Не вдалося завантажити розмову';
      set({ error: message, messagesLoading: false });
    }
  },

  endConversation: async (id) => {
    const conv = await chatApi.endConversation(id);
    set((s) => ({
      activeConversation: s.activeConversation?.id === id ? conv : s.activeConversation,
      conversations: s.conversations.map((c) =>
        c.id === id ? { ...c, status: 'ended' as const, ended_at: conv.ended_at } : c,
      ),
    }));
  },

  deleteConversation: async (id) => {
    await chatApi.deleteConversation(id);
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
      activeConversation: s.activeConversation?.id === id ? null : s.activeConversation,
      messages: s.activeConversation?.id === id ? [] : s.messages,
    }));
  },

  sendMessage: async (content) => {
    set({ sending: true });
    try {
      const msg = await chatApi.sendMessage(get().activeConversation!.id, content);
      set((s) => ({
        messages: [...s.messages, msg],
        sending: false,
        // Оновлюємо прев'ю в списку розмов
        conversations: s.conversations.map((c) =>
          c.id === msg.conversation_id
            ? { ...c, last_message_preview: content.slice(0, 100), message_count: c.message_count + 1 }
            : c,
        ),
      }));
      return msg;
    } catch {
      set({ sending: false });
      throw new Error('Не вдалося надіслати повідомлення');
    }
  },

  addMessage: (msg) => {
    set((s) => ({
      messages: [...s.messages, msg],
      botTyping: false,
      streamingContent: '',  // Очищаємо streaming буфер коли прийшло фінальне повідомлення
      conversations: s.conversations.map((c) =>
        c.id === msg.conversation_id
          ? { ...c, last_message_preview: msg.content.slice(0, 100), message_count: c.message_count + 1 }
          : c,
      ),
    }));
  },

  addOptimisticUserMessage: (content, conversationId) => {
    const tempId = `optimistic-${crypto.randomUUID()}`;
    const msg: ChatMessage = {
      id: tempId,
      conversation_id: conversationId,
      sender: 'user',
      content,
      sent_at: new Date().toISOString(),
      crisis_level: 'none',
      is_crisis: false,
    };
    set((s) => ({
      messages: [...s.messages, msg],
      conversations: s.conversations.map((c) =>
        c.id === conversationId
          ? { ...c, last_message_preview: content.slice(0, 100), message_count: c.message_count + 1 }
          : c,
      ),
    }));
    return tempId;
  },

  setBotTyping: (typing) => set({ botTyping: typing }),

  appendStreamChunk: (chunk) =>
    set((s) => ({
      streamingContent: s.streamingContent + chunk,
      botTyping: false,  // Коли є streaming — typing indicator прибираємо
    })),

  finalizeStream: () => set({ streamingContent: '', botTyping: false }),

  clearActiveConversation: () =>
    set({ activeConversation: null, messages: [], botTyping: false, streamingContent: '' }),
}));

