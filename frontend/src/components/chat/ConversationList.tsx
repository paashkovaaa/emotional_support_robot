import { formatDistanceToNow, parseISO } from 'date-fns';
import { uk } from 'date-fns/locale';
import { MessageCircle, Plus, Trash2 } from 'lucide-react';
import type { ConversationListItem } from '../../api/chat';

interface ConversationListProps {
  conversations: ConversationListItem[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onCreate,
  onDelete,
}: ConversationListProps) {
  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800">
      {/* Header */}
      <div className="p-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200">Розмови</h2>
        <button
          onClick={onCreate}
          className="w-8 h-8 bg-primary-50 hover:bg-primary-100 dark:bg-primary-900/30 dark:hover:bg-primary-900/50 rounded-lg
                     flex items-center justify-center text-primary-600 dark:text-primary-400 transition-colors"
          title="Нова розмова"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-6 text-center">
            <MessageCircle className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
            <p className="text-sm text-gray-400 dark:text-gray-500">Розмов поки немає</p>
            <button
              onClick={onCreate}
              className="mt-3 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 font-medium"
            >
              Почати першу розмову
            </button>
          </div>
        ) : (
          <div className="py-1">
            {conversations.map((conv) => {
              const isActive = conv.id === activeId;
              const isEnded = conv.status === 'ended';
              const timeAgo = formatDistanceToNow(parseISO(conv.started_at), {
                addSuffix: true,
                locale: uk,
              });

              return (
                <div
                  key={conv.id}
                  onClick={() => onSelect(conv.id)}
                  className={`group px-3 py-2.5 mx-1.5 rounded-lg cursor-pointer transition-all
                    ${isActive
                      ? 'bg-primary-50 border border-primary-200 dark:bg-primary-900/30 dark:border-primary-800'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent'
                    }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p
                        className={`text-sm font-medium truncate
                          ${isActive
                            ? 'text-primary-700 dark:text-primary-300'
                            : 'text-gray-700 dark:text-gray-200'
                          }
                          ${isEnded ? 'opacity-60' : ''}`}
                      >
                        {conv.title || 'Нова розмова'}
                      </p>
                      {conv.last_message_preview && (
                        <p className="text-xs text-gray-400 dark:text-gray-500 truncate mt-0.5">
                          {conv.last_message_preview}
                        </p>
                      )}
                      <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">
                        {timeAgo}
                        {isEnded && ' • завершена'}
                        {conv.message_count > 0 && ` • ${conv.message_count} пов.`}
                      </p>
                    </div>

                    {/* Delete button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 w-6 h-6 rounded
                                 flex items-center justify-center text-gray-400
                                 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 transition-all"
                      title="Видалити"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
