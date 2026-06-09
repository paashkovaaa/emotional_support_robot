import { useCallback, useEffect, useRef, useState } from 'react';

export interface WSMessage {
  type: 'message' | 'chunk' | 'typing' | 'error' | 'conversation_ended';
  content?: string | null;
  sender?: 'user' | 'bot' | null;
  message_id?: string | null;
  is_crisis?: boolean;
  crisis_level?: string | null;
}

interface UseWebSocketOptions {
  conversationId: string | null;
  onMessage?: (msg: WSMessage) => void;
  onTyping?: () => void;
  onError?: (error: string) => void;
  onConversationEnded?: () => void;
}

export function useWebSocket({
  conversationId,
  onMessage,
  onTyping,
  onError,
  onConversationEnded,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (!conversationId) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    const apiBase = import.meta.env.VITE_API_URL || window.location.origin;
    const wsBase = apiBase.replace(/^http/, 'ws');
    const url = `${wsBase}/api/chat/ws/chat/${conversationId}?token=${token}`;

    setConnecting(true);

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setConnecting(false);
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);

        switch (msg.type) {
          case 'message':
          case 'chunk':
            onMessage?.(msg);
            break;
          case 'typing':
            onTyping?.();
            break;
          case 'error':
            onError?.(msg.content || 'Невідома помилка');
            break;
          case 'conversation_ended':
            onConversationEnded?.();
            break;
        }
      } catch {
        // Ігноруємо невалідний JSON
      }
    };

    ws.onclose = (event) => {
      setConnected(false);
      setConnecting(false);
      wsRef.current = null;

      // Автоматичне перепідключення (якщо не навмисне закриття)
      if (event.code !== 1000 && event.code !== 4001) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      }
    };

    ws.onerror = () => {
      setConnected(false);
      setConnecting(false);
    };
  }, [conversationId, onMessage, onTyping, onError, onConversationEnded]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000);
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'message', content }));
    }
  }, []);

  const endConversation = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_conversation' }));
    }
  }, []);

  // Автопідключення при зміні conversationId
  useEffect(() => {
    if (conversationId) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [conversationId]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    connected,
    connecting,
    sendMessage,
    endConversation,
    disconnect,
    connect,
  };
}

