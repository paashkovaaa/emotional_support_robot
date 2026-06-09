import { useState, useEffect } from 'react';
import { X, Plus, Sparkles } from 'lucide-react';
import { EMOTION_EMOJIS, EMOTION_TAGS } from '../../utils/constants';
import type { EmotionEntry, EmotionEntryCreate, EmotionEntryUpdate } from '../../types';

interface Props {
  /** Дата запису (YYYY-MM-DD) */
  date: string;
  /** Існуючий запис (якщо редагуємо) */
  existingEntry?: EmotionEntry | null;
  /** Зберегти */
  onSave: (data: EmotionEntryCreate | EmotionEntryUpdate) => Promise<void>;
  /** Скасувати */
  onCancel: () => void;
  /** Запропонувати AI опис */
  onRequestBotSuggestion?: () => void;
  /** Чи йде збереження */
  saving?: boolean;
}

export default function EmotionForm({
  date,
  existingEntry,
  onSave,
  onCancel,
  onRequestBotSuggestion,
  saving = false,
}: Props) {
  const [emoji, setEmoji] = useState<string | null>(existingEntry?.emoji ?? null);
  const [description, setDescription] = useState(existingEntry?.user_description ?? '');
  const [botDescription] = useState(existingEntry?.bot_description ?? '');
  const [selectedTags, setSelectedTags] = useState<string[]>(existingEntry?.emotion_tags ?? []);
  const [customTag, setCustomTag] = useState('');
  const [showAllEmojis, setShowAllEmojis] = useState(false);

  const isEditing = !!existingEntry;

  // Скидаємо форму при зміні дати
  useEffect(() => {
    if (existingEntry) {
      setEmoji(existingEntry.emoji);
      setDescription(existingEntry.user_description ?? '');
      setSelectedTags(existingEntry.emotion_tags ?? []);
    } else {
      setEmoji(null);
      setDescription('');
      setSelectedTags([]);
    }
  }, [existingEntry, date]);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  };

  const addCustomTag = () => {
    const trimmed = customTag.trim().toLowerCase();
    if (trimmed && !selectedTags.includes(trimmed) && selectedTags.length < 10) {
      setSelectedTags((prev) => [...prev, trimmed]);
      setCustomTag('');
    }
  };

  const handleSubmit = async () => {
    if (isEditing) {
      const update: EmotionEntryUpdate = {
        emoji,
        user_description: description || null,
        emotion_tags: selectedTags.length > 0 ? selectedTags : null,
      };
      await onSave(update);
    } else {
      const create: EmotionEntryCreate = {
        entry_date: date,
        emoji,
        user_description: description || null,
        emotion_tags: selectedTags.length > 0 ? selectedTags : null,
      };
      await onSave(create);
    }
  };

  const displayedEmojis = showAllEmojis ? EMOTION_EMOJIS : EMOTION_EMOJIS.slice(0, 8);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-semibold text-gray-800">
          {isEditing ? 'Редагувати запис' : 'Новий запис'}
        </h3>
        <button
          onClick={onCancel}
          className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label="Закрити"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <p className="text-sm text-gray-500 mb-4">📅 {date}</p>

      {/* Вибір емодзі */}
      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Як ви себе почуваєте?
        </label>
        <div className="flex flex-wrap gap-2">
          {displayedEmojis.map(({ emoji: em, label }) => (
            <button
              key={em}
              onClick={() => setEmoji(emoji === em ? null : em)}
              title={label}
              className={`
                w-11 h-11 text-xl rounded-xl flex items-center justify-center
                transition-all duration-150 border-2
                ${emoji === em
                  ? 'border-primary-500 bg-primary-50 scale-110 shadow-sm'
                  : 'border-transparent hover:bg-gray-50 hover:border-gray-200'
                }
              `}
            >
              {em}
            </button>
          ))}
          <button
            onClick={() => setShowAllEmojis(!showAllEmojis)}
            className="w-11 h-11 text-xs text-gray-400 rounded-xl border-2 border-dashed border-gray-200 hover:border-gray-300 hover:text-gray-500 transition-all flex items-center justify-center"
          >
            {showAllEmojis ? 'менше' : '...'}
          </button>
        </div>
      </div>

      {/* Опис */}
      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Опишіть свій стан
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Як пройшов ваш день? Що відчуваєте?"
          rows={4}
          maxLength={5000}
          className="w-full px-4 py-3 border border-gray-200 rounded-xl resize-none
                     focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent
                     text-sm text-gray-700 placeholder-gray-400 transition-all"
        />
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-400">
            {description.length} / 5000
          </span>
          {onRequestBotSuggestion && (
            <button
              onClick={onRequestBotSuggestion}
              className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Запропонувати AI
            </button>
          )}
        </div>
      </div>

      {/* Опис від бота (якщо є) */}
      {botDescription && (
        <div className="mb-5 p-3 bg-accent-50 border border-accent-200 rounded-xl">
          <p className="text-xs font-medium text-accent-700 mb-1">🤖 Опис від Emi:</p>
          <p className="text-sm text-accent-800">{botDescription}</p>
        </div>
      )}

      {/* Теги */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Теги емоцій
        </label>
        <div className="flex flex-wrap gap-2 mb-3">
          {EMOTION_TAGS.map((tag) => (
            <button
              key={tag}
              onClick={() => toggleTag(tag)}
              className={`
                px-3 py-1.5 text-xs rounded-full transition-all border
                ${selectedTags.includes(tag)
                  ? 'bg-primary-100 text-primary-700 border-primary-300'
                  : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'
                }
              `}
            >
              {tag}
            </button>
          ))}
        </div>

        {/* Додати свій тег */}
        <div className="flex gap-2">
          <input
            value={customTag}
            onChange={(e) => setCustomTag(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addCustomTag()}
            placeholder="Свій тег..."
            maxLength={50}
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary-400
                       focus:border-transparent"
          />
          <button
            onClick={addCustomTag}
            disabled={!customTag.trim()}
            className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Plus className="w-4 h-4 text-gray-600" />
          </button>
        </div>

        {/* Обрані теги */}
        {selectedTags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {selectedTags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs"
              >
                {tag}
                <button
                  onClick={() => toggleTag(tag)}
                  className="hover:text-primary-900 ml-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Кнопки */}
      <div className="flex gap-3">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="flex-1 py-2.5 px-4 bg-primary-600 hover:bg-primary-700 text-white
                     rounded-xl font-medium text-sm transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Збереження...' : isEditing ? 'Оновити' : 'Зберегти'}
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-600
                     rounded-xl font-medium text-sm transition-colors"
        >
          Скасувати
        </button>
      </div>
    </div>
  );
}

