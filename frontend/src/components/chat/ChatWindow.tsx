import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import ChatInput from './ChatInput';
import EmiAvatar from './EmiAvatar';
import type { ChatMessage } from '../../api/chat';

interface ChatWindowProps {
  messages: ChatMessage[];
  loading: boolean;
  sending: boolean;
  botTyping: boolean;
  /** Поточний стримінговий текст від AI (chunk by chunk) */
  streamingContent?: string;
  conversationEnded: boolean;
  onSend: (content: string) => void;
}

export default function ChatWindow({
  messages,
  loading,
  sending,
  botTyping,
  streamingContent = '',
  conversationEnded,
  onSend,
}: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Автоскрол при нових повідомленнях або chunks
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, botTyping, streamingContent]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
          <p className="text-sm text-gray-500">Завантаження повідомлень...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 relative">
        {/* Emi background watermark — always visible */}
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center z-0">
          <EmiAvatar size={280} state={botTyping || !!streamingContent ? 'typing' : 'idle'} className="opacity-[0.12]" />
        </div>

        {messages.length === 0 && !streamingContent ? (
          <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-4">
            <div className="mb-5">
              <EmiAvatar size={160} state="idle" />
            </div>
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">
              Привіт! 👋
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed max-w-sm">
              Я — Emi, ваш віртуальний помічник для емоційної підтримки.
              Розкажіть, як ви себе почуваєте, і я спробую допомогти. 💙
            </p>
          </div>
        ) : (
          <div className="relative z-10 space-y-3 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Typing indicator */}
            {botTyping && !streamingContent && <TypingIndicator />}

            {/* Streaming bubble */}
            {streamingContent && (
              <div className="flex items-end gap-2.5">
                <div className="flex-shrink-0">
                  <EmiAvatar size={36} state="typing" />
                </div>
                <div className="max-w-[75%] bg-white dark:bg-gray-800 rounded-2xl rounded-bl-sm
                                px-4 py-3 shadow-sm border border-gray-100 dark:border-gray-700 text-sm
                                text-gray-800 dark:text-gray-100 leading-relaxed whitespace-pre-wrap">
                  {streamingContent}
                  <span className="inline-block w-0.5 h-4 bg-primary-400
                                   ml-0.5 align-middle animate-pulse" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      {conversationEnded ? (
        <div className="border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 p-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Ця розмова завершена. Створіть нову, щоб продовжити.
          </p>
        </div>
      ) : (
        <div className="max-w-3xl mx-auto w-full">
          <ChatInput onSend={onSend} sending={sending} />
        </div>
      )}
    </div>
  );
}
