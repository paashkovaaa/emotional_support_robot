import { useState } from 'react';
import { X, Sparkles, Save, Pencil } from 'lucide-react';
import type { EmotionGenerateResponse } from '../../types';

interface Props {
  suggestion: EmotionGenerateResponse;
  loading?: boolean;
  onSave: (data: { emoji: string; description: string; tags: string[] }) => void;
  onCancel: () => void;
}

export default function BotSuggestionModal({
  suggestion,
  loading = false,
  onSave,
  onCancel,
}: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [emoji, setEmoji] = useState(suggestion.emoji);
  const [description, setDescription] = useState(suggestion.description);
  const [tags, setTags] = useState<string[]>(suggestion.tags);

  const removeTag = (tag: string) => setTags((prev) => prev.filter((t) => t !== tag));

  const handleSave = () => {
    onSave({ emoji, description, tags });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in-95">
        {/* Close */}
        <button
          onClick={onCancel}
          className="absolute top-4 right-4 p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-2 mb-5">
          <div className="w-10 h-10 bg-accent-100 rounded-xl flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-accent-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Пропозиція Emi</h3>
            <p className="text-xs text-gray-500">На основі вашої останньої розмови</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center">
            <div className="inline-block w-8 h-8 border-3 border-accent-200 border-t-accent-600 rounded-full animate-spin mb-3" />
            <p className="text-sm text-gray-500">Emi аналізує розмову...</p>
          </div>
        ) : (
          <>
            {/* Emoji */}
            <div className="text-center mb-4">
              {isEditing ? (
                <input
                  value={emoji}
                  onChange={(e) => setEmoji(e.target.value)}
                  className="text-5xl text-center w-20 h-16 border border-gray-200 rounded-xl
                             focus:outline-none focus:ring-2 focus:ring-accent-400"
                  maxLength={4}
                />
              ) : (
                <span className="text-5xl">{emoji}</span>
              )}
            </div>

            {/* Description */}
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-1.5">Опис стану</p>
              {isEditing ? (
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm
                             focus:outline-none focus:ring-2 focus:ring-accent-400
                             resize-none"
                />
              ) : (
                <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 p-3 rounded-xl">
                  {description}
                </p>
              )}
            </div>

            {/* Tags */}
            <div className="mb-6">
              <p className="text-xs font-medium text-gray-500 mb-1.5">Теги</p>
              <div className="flex flex-wrap gap-1.5">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-accent-50 text-accent-700 rounded-full text-xs"
                  >
                    {tag}
                    {isEditing && (
                      <button onClick={() => removeTag(tag)} className="hover:text-accent-900">
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="flex-1 py-2.5 px-4 bg-accent-600 hover:bg-accent-700 text-white
                           rounded-xl font-medium text-sm flex items-center justify-center gap-2
                           transition-colors"
              >
                <Save className="w-4 h-4" />
                Зберегти
              </button>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="py-2.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-600
                           rounded-xl font-medium text-sm flex items-center gap-2
                           transition-colors"
              >
                <Pencil className="w-4 h-4" />
                {isEditing ? 'Готово' : 'Редагувати'}
              </button>
              <button
                onClick={onCancel}
                className="py-2.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-600
                           rounded-xl font-medium text-sm transition-colors"
              >
                Скасувати
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

