import { format, parseISO } from 'date-fns';
import { uk } from 'date-fns/locale';
import { User, AlertTriangle } from 'lucide-react';
import EmiAvatar from './EmiAvatar';
import type { ChatMessage } from '../../api/chat';

interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isBot = message.sender === 'bot';
  const isCrisis = message.is_crisis;

  const timeStr = format(parseISO(message.sent_at), 'HH:mm', { locale: uk });

  return (
    <div className={`flex gap-2.5 ${isBot ? 'justify-start' : 'justify-end'}`}>
      {/* Avatar (bot only) */}
      {isBot && (
        isCrisis ? (
          <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 mt-1 bg-red-100 dark:bg-red-900/40">
            <AlertTriangle className="w-4 h-4 text-red-500 dark:text-red-400" />
          </div>
        ) : (
          <div className="flex-shrink-0 mt-1">
            <EmiAvatar size={36} state="idle" />
          </div>
        )
      )}

      {/* Bubble */}
      <div className={`max-w-[75%] min-w-[60px]`}>
        <div
          className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap break-words
            ${isBot
              ? isCrisis
                ? 'bg-red-50 border border-red-200 text-gray-800 rounded-tl-md dark:bg-red-950/30 dark:border-red-800 dark:text-gray-100'
                : 'bg-white border border-gray-100 text-gray-800 shadow-sm rounded-tl-md dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100'
              : 'bg-primary-600 text-white rounded-tr-md dark:bg-primary-700'
            }`}
        >
          {message.content}
        </div>
        <p
          className={`text-[10px] mt-1 px-1 text-gray-400 dark:text-gray-500
            ${isBot ? 'text-left' : 'text-right'}`}
        >
          {timeStr}
        </p>
      </div>

      {/* Avatar (user only) */}
      {!isBot && (
        <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-primary-600 dark:text-primary-400" />
        </div>
      )}
    </div>
  );
}
