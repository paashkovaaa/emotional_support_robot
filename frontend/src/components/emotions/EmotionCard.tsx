import { Pencil, Trash2, Calendar } from 'lucide-react';
import { formatDateLong } from '../../utils/formatters';
import type { EmotionEntry } from '../../types';

interface Props {
  entry: EmotionEntry;
  onEdit: () => void;
  onDelete: () => void;
  deleting?: boolean;
}

export default function EmotionCard({ entry, onEdit, onDelete, deleting = false }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      {/* Заголовок */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {entry.emoji && (
            <span className="text-4xl">{entry.emoji}</span>
          )}
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Запис за день</h3>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
              <Calendar className="w-3.5 h-3.5" />
              {formatDateLong(entry.entry_date)}
            </p>
          </div>
        </div>

        {/* Дії */}
        <div className="flex gap-1">
          <button
            onClick={onEdit}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Редагувати"
          >
            <Pencil className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={onDelete}
            disabled={deleting}
            className="p-2 hover:bg-red-50 rounded-lg transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
            title="Видалити"
          >
            <Trash2 className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </div>

      {/* Опис від користувача */}
      {entry.user_description && (
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500 mb-1.5">Ваш опис</p>
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {entry.user_description}
          </p>
        </div>
      )}

      {/* Опис від бота */}
      {entry.bot_description && (
        <div className="mb-4 p-3 bg-accent-50 border border-accent-100 rounded-xl">
          <p className="text-xs font-medium text-accent-600 mb-1">🤖 Опис від Emi</p>
          <p className="text-sm text-accent-800 leading-relaxed">
            {entry.bot_description}
          </p>
        </div>
      )}

      {/* Теги */}
      {entry.emotion_tags && entry.emotion_tags.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">Теги</p>
          <div className="flex flex-wrap gap-1.5">
            {entry.emotion_tags.map((tag) => (
              <span
                key={tag}
                className="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Порожній стан */}
      {!entry.user_description && !entry.bot_description && !entry.emoji && (
        <p className="text-sm text-gray-400 text-center py-4">
          Запис без деталей. Натисніть «Редагувати», щоб додати інформацію.
        </p>
      )}
    </div>
  );
}

