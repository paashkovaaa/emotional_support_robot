import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  sending?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  disabled = false,
  sending = false,
  placeholder = 'Напишіть повідомлення...',
}: ChatInputProps) {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled || sending) return;
    onSend(trimmed);
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 p-3 flex items-end gap-2"
    >
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none px-3.5 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl text-sm
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500
                   transition placeholder:text-gray-400 dark:placeholder:text-gray-500 disabled:bg-gray-50 dark:disabled:bg-gray-850
                   max-h-32 overflow-y-auto"
        style={{ minHeight: '42px' }}
        onInput={(e) => {
          const target = e.target as HTMLTextAreaElement;
          target.style.height = 'auto';
          target.style.height = Math.min(target.scrollHeight, 128) + 'px';
        }}
      />
      <button
        type="submit"
        disabled={!text.trim() || disabled || sending}
        className="w-10 h-10 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-200
                   text-white disabled:text-gray-400 rounded-xl flex items-center justify-center
                   transition-colors flex-shrink-0"
      >
        {sending ? (
          <Loader2 className="w-4.5 h-4.5 animate-spin" />
        ) : (
          <Send className="w-4.5 h-4.5" />
        )}
      </button>
    </form>
  );
}
