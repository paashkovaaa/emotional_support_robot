import { useEffect, useCallback, useState } from 'react';
import { PanelLeftClose, PanelLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { useChatStore } from '../stores/chatStore';
import { ConversationList, ChatWindow } from '../components/chat';
import EmiAvatar from '../components/chat/EmiAvatar';
import { useWebSocket } from '../hooks/useWebSocket';
import type { WSMessage } from '../hooks/useWebSocket';

export default function ChatPage() {
  const {
    conversations,
    activeConversation,
    messages,
    messagesLoading,
    sending,
    botTyping,
    streamingContent,
    fetchConversations,
    createConversation,
    selectConversation,
    endConversation,
    deleteConversation,
    sendMessage: sendRestMessage,
    addMessage,
    addOptimisticUserMessage,
    setBotTyping,
    appendStreamChunk,
    finalizeStream,
  } = useChatStore();

  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Завантажуємо розмови при монтуванні
  useEffect(() => {
    fetchConversations();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // WebSocket handlers
  const handleWSMessage = useCallback(
    (msg: WSMessage) => {
      if (!activeConversation) return;

      if (msg.type === 'chunk' && msg.content) {
        // Стримінговий chunk — додаємо до streaming буфера
        appendStreamChunk(msg.content);
        return;
      }

      if (msg.type === 'message' && msg.sender === 'bot' && msg.content) {
        // Фінальне повідомлення бота — додаємо до списку і очищаємо streaming
        addMessage({
          id: msg.message_id || crypto.randomUUID(),
          conversation_id: activeConversation.id,
          sender: 'bot',
          content: msg.content,
          sent_at: new Date().toISOString(),
          crisis_level: (msg.crisis_level as any) || 'none',
          is_crisis: msg.is_crisis || false,
        });
        // finalizeStream() вже викликається всередині addMessage
      }
    },
    [activeConversation, addMessage, appendStreamChunk],
  );

  const handleWSTyping = useCallback(() => {
    setBotTyping(true);
  }, [setBotTyping]);

  const handleWSError = useCallback(
    (error: string) => {
      toast.error(error);
      finalizeStream();
      setBotTyping(false);
    },
    [setBotTyping, finalizeStream],
  );

  const handleWSConversationEnded = useCallback(() => {
    if (activeConversation) {
      fetchConversations();
      selectConversation(activeConversation.id);
    }
  }, [activeConversation, fetchConversations, selectConversation]);

  // WebSocket connection
  const { connected, sendMessage: wsSendMessage } = useWebSocket({
    conversationId: activeConversation?.status === 'active' ? activeConversation.id : null,
    onMessage: handleWSMessage,
    onTyping: handleWSTyping,
    onError: handleWSError,
    onConversationEnded: handleWSConversationEnded,
  });

  // Створення нової розмови
  const handleNewConversation = async () => {
    try {
      await createConversation();
    } catch {
      toast.error('Не вдалося створити розмову');
    }
  };

  // Вибір розмови
  const handleSelectConversation = (id: string) => {
    selectConversation(id);
  };

  // Видалення розмови
  const handleDeleteConversation = async (id: string) => {
    const confirmed = window.confirm('Видалити цю розмову?');
    if (!confirmed) return;
    try {
      await deleteConversation(id);
      toast.success('Розмову видалено');
    } catch {
      toast.error('Не вдалося видалити розмову');
    }
  };

  // Надсилання повідомлення
  const handleSend = async (content: string) => {
    if (!activeConversation) return;

    if (connected) {
      // ── Основний шлях: через WebSocket ──
      // Додаємо повідомлення в UI одразу (оптимістично)
      addOptimisticUserMessage(content, activeConversation.id);
      setBotTyping(true);
      // Надсилаємо через WS — бекенд збереже і поверне AI-відповідь
      wsSendMessage(content);
    } else {
      // ── Fallback: через REST (без streaming) ──
      try {
        await sendRestMessage(content);
        setBotTyping(true);
        // AI-відповідь (якщо є) збережена в БД, реакція буде після reconnect
        setTimeout(() => setBotTyping(false), 3000);
      } catch {
        toast.error('Не вдалося надіслати повідомлення');
      }
    }
  };

  return (
    <div className="h-full flex">
      {/* Sidebar з розмовами */}
      <div
        className={`transition-all duration-200 flex-shrink-0
          ${sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'}`}
      >
        <ConversationList
          conversations={conversations}
          activeId={activeConversation?.id || null}
          onSelect={handleSelectConversation}
          onCreate={handleNewConversation}
          onDelete={handleDeleteConversation}
        />
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mini header inside chat */}
        <div className="h-11 border-b border-gray-100 bg-white/50 flex items-center px-3 gap-2 flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center
                       text-gray-500 transition-colors"
            title={sidebarOpen ? 'Сховати розмови' : 'Показати розмови'}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-4 h-4" />
            ) : (
              <PanelLeft className="w-4 h-4" />
            )}
          </button>

          {activeConversation && (
            <div className="flex-1 min-w-0 flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-700 truncate">
                {activeConversation.title || 'Нова розмова'}
              </h3>
              {connected && (
                <span className="w-2 h-2 bg-green-400 rounded-full flex-shrink-0" title="Підключено" />
              )}
              {activeConversation.status === 'ended' && (
                <span className="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                  завершена
                </span>
              )}
            </div>
          )}

          {activeConversation?.status === 'active' && (
            <button
              onClick={() => endConversation(activeConversation.id)}
              className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded
                         hover:bg-gray-100 transition-colors"
            >
              Завершити
            </button>
          )}
        </div>

        {/* Chat window or empty state */}
        {activeConversation ? (
          <ChatWindow
            messages={messages}
            loading={messagesLoading}
            sending={sending}
            botTyping={botTyping}
            streamingContent={streamingContent}
            conversationEnded={activeConversation.status === 'ended'}
            onSend={handleSend}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center px-4">
              <div className="flex justify-center mb-4">
                <EmiAvatar size={96} state="idle" />
              </div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                {conversations.length > 0
                  ? 'Оберіть розмову'
                  : 'Почніть розмову'}
              </h3>
              <p className="text-sm text-gray-500 max-w-sm leading-relaxed mb-4">
                {conversations.length > 0
                  ? 'Виберіть існуючу розмову зліва або створіть нову.'
                  : 'Створіть першу розмову з Emi — вашим помічником для емоційної підтримки.'}
              </p>
              <button
                onClick={handleNewConversation}
                className="px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white
                           font-medium rounded-xl text-sm transition-colors"
              >
                Нова розмова
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

